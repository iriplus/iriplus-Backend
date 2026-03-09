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


def build_student_prompt(
    level: str,
    source_text: str,
    exercise_list_text: str,
    retrieved_context: str,
) -> str:
    """
    Build the prompt used to generate a student exam from a generic source text.

    IMPORTANT:
    - The returned question must already contain blanks / gaps so it can be
      rendered directly in the frontend for the student to complete.
    - The correct answer must be returned separately in the 'answer' field.
    """

    return f"""
You are an expert Cambridge English exam designer.

Level: {level}

Source text:
{source_text}

Retrieved historical exams from this course
(use only as structural guidance, never copy content):
{retrieved_context}

Requested exercise types in this exact order:
{exercise_list_text}

You are generating an exam for a STUDENT to solve directly in the frontend.

Critical formatting rules:
- Every requested exercise type MUST appear exactly once.
- Preserve the SAME ORDER as the requested exercise types.
- The exam must be based on the source text.
- Content must be original.
- Difficulty must strictly match the Cambridge level.
- All content must be in English.
- Output STRICT JSON only.
- Do NOT include explanations outside JSON.
- Each item MUST contain:
  - "question": the visible version shown to the student
  - "answer": the hidden correct answer stored in backend
- The "question" field MUST already contain a blank gap using underscores, such as:
  - _____
  - __________
- Each exercise block MUST include clear student-facing instructions.
- "instructions" must never be empty.
- The correct answer MUST NOT appear written inside the visible question text.
- If the exercise is a gap-fill / cloze / word formation / transformation, replace the answer location with underscores.
- If the item includes a prompt word, keyword, base word, or options, those may remain visible.
- The "answer" field must contain only the correct answer text, with no labels, no explanations, and no brackets.
- For "Open cloze test", do NOT include multiple-choice options.
- For "Cloze test with options", each question must include the answer options inside the visible question text.
- For "Key word transformation", the visible question must include the sentence with a blank and the key word.
- For "Word Formation", the visible question must include the base word and a blank in the sentence.
- The value of "exercise_type" should match the requested type as closely as possible, but preserving order is more important than exact naming.

Examples:

Word Formation item:
{{
  "question": "Online learning has made education more accessible and ____________ (DIVERSIFY) for people with different needs and backgrounds.",
  "answer": "diverse"
}}

Open Cloze item:
{{
  "question": "Students can now study at their own ____________.",
  "answer": "pace"
}}

Key Word Transformation item:
{{
  "question": "He stopped ____________ and then he carried on studying. TAKE",
  "answer": "taking a rest"
}}

Multiple Choice Cloze item:
{{
  "question": "Online learning has made education more ____________ (A) inclusive / exclusive / distant / private",
  "answer": "inclusive"
}}

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


def build_student_scoring_prompt(
    level: str,
    exam_snapshot: str,
    student_answer: str,
) -> str:
    """
    Build the prompt used to score a student's submitted exam.
    """

    return f"""
You are an expert Cambridge English examiner.

Level: {level}

Official generated exam with correct answers:
{exam_snapshot}

Student submitted answers:
{student_answer}

Scoring rules:
- Grade the exam on a scale from 0 to 100.
- Be pedagogically fair.
- Compare each student answer against the corresponding correct answer.
- Accept minor spelling variations only when they do not change the intended answer.
- Accept equivalent valid answers when the exercise type allows it.
- Do not invent missing answers.
- Output STRICT JSON only.
- Do NOT include explanations outside JSON.

Required JSON schema:

{{
  "score": 0
}}
"""


def generate_text_from_llm(prompt: str) -> str:
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


def generate_score_from_llm(prompt: str) -> str:
    """
    Wrapper for scoring student submissions.
    """

    return generate_text_from_llm(prompt)
