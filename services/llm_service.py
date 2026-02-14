"""
LLM service for generating exams.

This module encapsulates:
- Prompt construction
- Model invocation (Ollama)
"""

import os
from typing import cast
import requests

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

def build_refinement_prompt(
    level: str,
    original_snapshot: str,
    teacher_feedback: str,
) -> str:
    """
    Build the prompt for refining an already generated exam
    based on teacher feedback.

    The model must modify the existing exam, not recreate it
    from scratch unless explicitly required by the feedback.
    """

    return f"""
You are an expert Cambridge English exam designer.

Level: {level}

Here is the CURRENT generated exam (JSON):
{original_snapshot}

Teacher requested changes:
{teacher_feedback}

Refinement rules:
- You MUST keep the same exercise types unless the teacher explicitly asks to change them.
- You MUST preserve the general structure of the exam.
- Modify only what is necessary to satisfy the teacher feedback.
- Do NOT remove exercises unless explicitly requested.
- Do NOT add new exercise types unless explicitly requested.
- Difficulty must strictly match the Cambridge level.
- All content must remain original and in English.
- Keep the output consistent and pedagogically valid.
- Output STRICT JSON.
- Do NOT include explanations outside JSON.

Required JSON schema (must be identical):

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
