"""
LLM service for generating exams.

This module encapsulates:
- Prompt construction
- Model invocation (Ollama)
"""

import requests
import os
from typing import cast

OLLAMA_URL = cast(str, os.getenv("OLLAMA_URL"))
MODEL_NAME = cast(str, os.getenv("OLLAMA_MODEL"))
if not OLLAMA_URL or not MODEL_NAME:
    raise ValueError("OLLAMA_URL and OLLAMA_MODEL must be defined in .env")


def build_prompt(
    level: str,
    teacher_text: str,
    exercise_list_text: str,
    retrieved_context: str,
) -> str:
    """
    Build the prompt sent to the LLM.
    """

    return f"""
You are an expert Cambridge English exam designer.

Level: {level}

Teacher source text:
{teacher_text}

Retrieved historical exams from this course
(use only as structural guidance, never copy content):
{retrieved_context}

Requested exercise types:
{exercise_list_text}

Rules:
- Every requested exercise type MUST appear.
- Content must be original.
- Difficulty must strictly match the Cambridge level.
- All content must be in English.
- Output STRICT JSON.
- Do NOT include explanations outside JSON.

Required JSON schema:

{{
  "exercises": [
    {{
      "exercise_type": "string",
      "instructions": "string",
      "items": [
        {{
          "question": "string",
          "answer": "string"
        }}
      ]
    }}
  ]
}}
"""


def generate_exam_from_llm(prompt: str) -> str:
    """
    Call the LLM and return raw output text.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5
            }
        },
        timeout=300,
    )

    response.raise_for_status()

    return response.json()["response"]
