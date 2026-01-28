"""
RAG service for retrieving historical exam context from Qdrant.

This module encapsulates:
- SentenceTransformer embeddings
- Qdrant vector search
- Course-level filtering
"""

from typing import List
import requests
from sentence_transformers import SentenceTransformer
import os


QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION")

if not QDRANT_URL or not COLLECTION_NAME:
    raise ValueError("QDRANT_URL and QDRANT_COLLECTION must be defined in .env")

# Load once at module import (important for performance)
_embedder = SentenceTransformer("BAAI/bge-base-en-v1.5")


def retrieve_course_context(
    course_id: str,
    level: str,
    exercises_description: str,
    k: int = 15,
) -> List[str]:
    """
    Retrieve relevant historical exam chunks for a given course.

    Args:
        course_id: Identifier of the course (used as Qdrant filter).
        level: Cambridge level of the class.
        exercises_description: Text describing requested exercises.
        k: Number of vector matches to retrieve.

    Returns:
        List of retrieved text chunks.
    """

    query_text = f"""
    Cambridge Level: {level}
    Exercises requested:
    {exercises_description}
    """

    query_vector = _embedder.encode(query_text).tolist()

    query = {
        "vector": query_vector,
        "limit": k,
        "with_payload": True,
        "filter": {
            "must": [
                {"key": "course_id", "match": {"value": course_id}}
            ]
        },
    }

    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
        json=query,
        timeout=15,
    )
    response.raise_for_status()

    hits = response.json().get("result", [])

    contexts: List[str] = []

    for hit in hits:
        payload = hit.get("payload")
        if payload and payload.get("text"):
            contexts.append(payload["text"])

    return contexts
