"""
Service for selecting a generic context for student exams.
"""

from __future__ import annotations

from pathlib import Path
import random


BASE_CONTEXTS_DIR = Path(__file__).resolve().parent.parent / "generic_contexts"

COURSE_BUCKET_KEYWORDS = {
    "kids": [
        "kids",
        "kid",
        "children",
        "child",
        "starters",
        "movers",
        "flyers",
        "grade",
        "junior"
    ],
    "teens": [
        "teens",
        "teen",
        "for schools",
        "schools",
        "adolescents",
        "adolescent",
        "adol",
        "first",
        "pre-first",
        "fce"
    ],
    "adults": [
        "adults",
        "adult",
        "cae",
        "prof",
        "proficiency",
        "workshop"
    ],
}


def resolve_course_bucket(course_name: str) -> str:
    """
    Resolve the generic context bucket from the course name.

    Fallback is 'teens' if no explicit match is found.
    """

    normalized = (course_name or "").strip().lower()
    if not normalized:
        raise ValueError("Course name is required to resolve the context bucket")

    for bucket, keywords in COURSE_BUCKET_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return bucket

    return "teens"


def get_random_generic_context(course_name: str) -> str:
    """
    Return a random generic context from the folder that matches the course.
    """

    bucket = resolve_course_bucket(course_name)
    bucket_dir = BASE_CONTEXTS_DIR / bucket

    if not bucket_dir.exists() or not bucket_dir.is_dir():
        raise FileNotFoundError(
            f"Generic context folder not found for bucket '{bucket}'"
        )

    candidates = [
        *bucket_dir.glob("*.txt"),
        *bucket_dir.glob("*.md"),
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No generic context files found inside '{bucket_dir}'"
        )

    selected_file = random.SystemRandom().choice(candidates)
    content = selected_file.read_text(encoding="utf-8").strip()

    if not content:
        raise ValueError(f"Selected context file '{selected_file.name}' is empty")

    return content