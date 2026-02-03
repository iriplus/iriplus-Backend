"""
RAG service for retrieving historical exam context from Qdrant.
"""

from typing import List
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


# ---- Environment variables ----

_qdrant_url = os.getenv("QDRANT_URL")
_collection_name = os.getenv("QDRANT_COLLECTION")

if _qdrant_url is None or _collection_name is None:
    raise ValueError("QDRANT_URL and QDRANT_COLLECTION must be defined in .env")

QDRANT_URL: str = _qdrant_url
COLLECTION_NAME: str = _collection_name

# ---- Load once at import ----

_embedder = SentenceTransformer("BAAI/bge-base-en-v1.5")
_client = QdrantClient(url=QDRANT_URL)

def retrieve_course_context(
    course_id: str,
    level: str,
    exercises_description: str,
    k: int = 5,
) -> List[str]:

    course_id = course_id.strip()
    query_text = f"""
    Cambridge Level: {level}
    Exercises requested:
    {exercises_description}
    """

    query_vector = _embedder.encode(query_text).tolist()

    # Properly typed filter
    qdrant_filter = Filter(
        must=[
            FieldCondition(
                key="course_id",
                match=MatchValue(value=course_id),
            )
        ]
    )

    result = _client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=k,
        with_payload=True,
        query_filter=qdrant_filter,
    )

    hits = result.points

    contexts: List[str] = []

    for i, hit in enumerate(hits, start=1):


        payload = hit.payload

        if not payload:
            continue

        text = payload.get("text")
        if text:
            preview = text[:200].replace("\n", " ")
            contexts.append(text)

    return contexts
