from __future__ import annotations

import json
import os
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import joinedload

from orm_models import Exam, ExamExerciseInstance
from utils.types_enum import ExamStatus

_qdrant_url = os.getenv("QDRANT_URL")
_collection_name = os.getenv("QDRANT_COLLECTION")

if _qdrant_url is None or _collection_name is None:
    raise ValueError("QDRANT_URL and QDRANT_COLLECTION must be defined in .env")

QDRANT_URL: str = _qdrant_url
COLLECTION_NAME: str = _collection_name
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

VECTOR_SIZE = 768
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBED_BATCH_SIZE = 64
UPSERT_BATCH_SIZE = 128

ACCEPTED_STATUS = ExamStatus.ACCEPTED.value
AI_SOURCE = "ai_generated_exam"

embedder = SentenceTransformer(EMBEDDING_MODEL)
client = QdrantClient(url=QDRANT_URL)


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def to_iso(value: Any) -> str | None:
    if value is None:
        return None

    try:
        return str(value.isoformat())
    except AttributeError:
        return str(value)


def json_obj_to_text(value: Any, indent: int = 0) -> str:
    prefix = "  " * indent

    if value is None:
        return ""

    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                nested = json_obj_to_text(item, indent + 1)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{prefix}{key}: {item}")
        return "\n".join(lines)

    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            if isinstance(item, (dict, list)):
                nested = json_obj_to_text(item, indent + 1)
                if nested:
                    lines.append(f"{prefix}-")
                    lines.append(nested)
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines)

    return f"{prefix}{value}"


def json_string_to_text(raw: str | None) -> str:
    if not raw:
        return ""

    try:
        parsed = json.loads(raw)
        return json_obj_to_text(parsed)
    except (TypeError, json.JSONDecodeError):
        return str(raw)


def get_exam_class_obj(exam: Exam) -> Any | None:
    return cast(Any | None, exam.class_exam)


def get_generated_exercises(exam: Exam) -> list[ExamExerciseInstance]:
    return cast(list[ExamExerciseInstance], exam.generated_exercises)


def get_exercise_type_obj(instance: ExamExerciseInstance) -> Any | None:
    return cast(Any | None, instance.exercise_type)


def resolve_course_name(exam: Exam) -> str:
    class_obj = get_exam_class_obj(exam)
    if class_obj is None:
        return f"class_{exam.class_id}"

    for attr in ("description", "name", "title"):
        value = getattr(class_obj, attr, None)
        if value:
            return str(value)

    return f"class_{exam.class_id}"


def resolve_exercise_type_name(instance: ExamExerciseInstance) -> str:
    exercise_type = get_exercise_type_obj(instance)
    if exercise_type is None:
        return "Unknown exercise type"

    name = getattr(exercise_type, "name", None)
    if name:
        return str(name)

    return f"exercise_type_{instance.exercise_type_id}"


def build_exam_document(exam: Exam) -> str:
    course_name = resolve_course_name(exam)

    sections: list[str] = [
        f"Exam ID: {exam.id}",
        f"Course ID: {exam.class_id}",
        f"Course Name: {course_name}",
        f"Status: {exam.status}",
    ]

    if getattr(exam, "context", None):
        sections.append("Context:")
        sections.append(str(exam.context))

    if getattr(exam, "notes", None):
        sections.append("Notes:")
        sections.append(str(exam.notes))

    exercises = sorted(
        get_generated_exercises(exam),
        key=lambda item: (
            getattr(item, "id", 0) or 0,
            item.exercise_type_id or 0,
        ),
    )

    for index, instance in enumerate(exercises, start=1):
        exercise_type_name = resolve_exercise_type_name(instance)

        sections.append(f"Exercise {index}")
        sections.append(f"Exercise Type: {exercise_type_name}")

        if instance.instructions:
            sections.append("Instructions:")
            sections.append(str(instance.instructions))

        content_text = json_string_to_text(instance.content_json)
        if content_text:
            sections.append("Content:")
            sections.append(content_text)

        answer_key_text = json_string_to_text(instance.answer_key_json)
        if answer_key_text:
            sections.append("Answer Key:")
            sections.append(answer_key_text)

    full_text = "\n\n".join(section for section in sections if section)
    return normalize_whitespace(full_text)


def exam_already_indexed(exam_id: int) -> bool:
    scroll_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value=AI_SOURCE),
            ),
            models.FieldCondition(
                key="exam_id",
                match=models.MatchValue(value=exam_id),
            ),
        ]
    )

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=scroll_filter,
        limit=1,
        with_payload=False,
        with_vectors=False,
    )

    return bool(points)


def build_point_id(exam_id: int, chunk_index: int) -> str:
    raw_id = f"{AI_SOURCE}:{exam_id}:{chunk_index}"
    return str(uuid5(NAMESPACE_URL, raw_id))


def vector_to_list(vector: Any) -> list[float]:
    raw_vector = vector.tolist() if hasattr(vector, "tolist") else vector
    return [float(item) for item in raw_vector]


def flush_points(points_buffer: list[models.PointStruct]) -> None:
    if not points_buffer:
        return

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points_buffer,
    )
    points_buffer.clear()


def index_exam(exam: Exam) -> int:
    document_text = build_exam_document(exam)
    if not document_text.strip():
        return 0

    chunks = chunk_text(document_text)
    if not chunks:
        return 0

    embeddings = cast(
        Any,
        embedder.encode(
            chunks,
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=False,
        ),
    )

    course_name = resolve_course_name(exam)
    doc_id = f"exam_{exam.id}"

    points_buffer: list[models.PointStruct] = []

    for chunk_index, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        point = models.PointStruct(
            id=build_point_id(exam.id, chunk_index),
            vector=vector_to_list(vector),
            payload={
                "source": AI_SOURCE,
                "course_id": exam.class_id,
                "course_name": course_name,
                "doc_id": doc_id,
                "exam_id": exam.id,
                "chunk_index": chunk_index,
                "status": exam.status,
                "coordinator_id": exam.coordinator_id,
                "user_id": exam.user_id,
                "created_at": to_iso(getattr(exam, "date_created", None)),
                "corrected_at": to_iso(getattr(exam, "corrected_at", None)),
                "student_submitted_at": to_iso(getattr(exam, "student_submitted_at", None)),
                "text": chunk,
            },
        )
        points_buffer.append(point)

        if len(points_buffer) >= UPSERT_BATCH_SIZE:
            flush_points(points_buffer)

    flush_points(points_buffer)
    return len(chunks)


def sync_accepted_exams_to_qdrant() -> dict[str, int]:
    exam_class_exam_rel = cast(Any, Exam.class_exam)
    exam_generated_exercises_rel = cast(Any, Exam.generated_exercises)
    exam_exercise_type_rel = cast(Any, ExamExerciseInstance.exercise_type)

    query = (
        Exam.query.options(
            joinedload(exam_class_exam_rel),
            joinedload(exam_generated_exercises_rel).joinedload(
                exam_exercise_type_rel
            ),
        )
        .filter(Exam.status == ACCEPTED_STATUS)
        .order_by(Exam.class_id.asc(), Exam.id.asc())
    )

    if hasattr(Exam, "date_deleted"):
        query = query.filter(Exam.date_deleted.is_(None))

    exams = cast(list[Exam], query.all())

    indexed_exams = 0
    indexed_chunks = 0
    skipped_already_indexed = 0
    skipped_empty = 0

    for exam in exams:
        if exam_already_indexed(exam.id):
            skipped_already_indexed += 1
            continue

        chunk_count = index_exam(exam)
        if chunk_count == 0:
            skipped_empty += 1
            continue

        indexed_exams += 1
        indexed_chunks += chunk_count

    result = {
        "accepted_found": len(exams),
        "indexed_exams": indexed_exams,
        "indexed_chunks": indexed_chunks,
        "skipped_already_indexed": skipped_already_indexed,
        "skipped_empty": skipped_empty,
    }

    print(result)
    return result