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
- For "Cloze test with options" and "Multiple Choice", each question must include the answer options inside the visible question text between parenthesis and separated by a /. For example: Online learning has made education more ____________ (inclusive / exclusive / distant / private).
- Do NOT include more than one gap per question.

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


def _format_previous_questions(previous_questions: list[str] | tuple[str, ...]) -> str:
    """Keep cross-exercise anti-duplication context compact."""
    if not previous_questions:
        return "None; this is the first exercise in the exam."

    recent_questions = previous_questions[-10:]
    return "\n".join(f"- {question[:300]}" for question in recent_questions)


def build_teacher_exercise_prompt(
    level: str,
    source_text: str,
    requested_exercises: str,
    exercise_name: str,
    exercise_description: str,
    retrieved_context: str,
    previous_questions: list[str] | tuple[str, ...],
) -> str:
    """Build a compact teacher prompt for exactly one exercise type."""
    historical_context = retrieved_context or "No historical context was retrieved."
    return f"""
You are an expert Cambridge English exam designer.

Shared exam context:
- Cambridge level: {level}
- All exercise types requested for this exam: {requested_exercises}

Teacher source text:
{source_text}

Retrieved historical course material
(structural guidance only; never copy its content):
{historical_context}

Generate ONLY this exercise type:
- Name: {exercise_name}
- Definition: {exercise_description}

Questions already generated for other exercise types
(do not repeat or closely paraphrase them):
{_format_previous_questions(previous_questions)}

Rules:
- Generate exactly one exercise block for the named type.
- Base the exercise on the teacher source text and keep it coherent with the shared exam context.
- Content must be original, in English, and strictly appropriate for the Cambridge level.
- Every item must contain exactly one solvable task, one question, and one answer.
- Do not include more than one gap per question.
- For "Cloze test with options" and "Multiple Choice", embed options in the question
  between parentheses and separate them with " / ". Do not create an options field.
- Output strict JSON only, with no text outside JSON.

Required JSON schema:
{{
  "exercise": {{
    "exercise_type": "{exercise_name}",
    "instructions": "string",
    "items": [
      {{"question": "string", "answer": "string"}}
    ]
  }}
}}
"""


def build_student_exercise_prompt(
    level: str,
    source_text: str,
    requested_exercises: str,
    exercise_name: str,
    exercise_description: str,
    retrieved_context: str,
    difficulty_band: str,
    previous_questions: list[str] | tuple[str, ...],
    target_item_count: int = 2,
) -> str:
    """Build a student-facing prompt for exactly one exercise type."""
    difficulty_instruction = {
        "easier": "Make it slightly easier within the level using clearer clues and common vocabulary.",
        "harder": "Make it slightly harder within the level using less obvious clues and stronger distractors.",
    }.get(difficulty_band, "Use the standard difficulty for the stated level.")
    historical_context = retrieved_context or "No historical context was retrieved."

    return f"""
You are an expert Cambridge English exam designer.

Shared exam context:
- Cambridge level: {level}
- Adaptive difficulty: {difficulty_instruction}
- All exercise types requested for this exam: {requested_exercises}

Source text:
{source_text}

Retrieved historical course material
(structural guidance only; never copy its content):
{historical_context}

Generate ONLY this exercise type:
- Name: {exercise_name}
- Definition: {exercise_description}
- Required number of items: {target_item_count}

Questions already generated for other exercise types
(do not repeat or closely paraphrase them):
{_format_previous_questions(previous_questions)}

Student-exam rules:
- Generate exactly one exercise block for the named type and exactly {target_item_count} items.
- Base every item on the source text and keep it coherent with the shared exam context.
- Content must be original, in English, and appropriate for the Cambridge level.
- Each item must have exactly the keys "question" and "answer".
- Each question must contain exactly one task and require exactly one answer.
- The visible question must use underscores for the answer location when the exercise uses a gap.
- The answer must contain only the hidden correct answer, without labels or explanations.
- Open cloze must not contain options.
- Cloze with options and Multiple Choice must embed options in the question between
  parentheses separated by " / "; never create an options field.
- Key word transformation must show the key word and the sentence with a gap.
- Word Formation must show the base word and the sentence with a gap.
- Output strict JSON only, with no text outside JSON.

Required JSON schema:
{{
  "exercise": {{
    "exercise_type": "{exercise_name}",
    "instructions": "string",
    "items": [
      {{"question": "string", "answer": "string"}}
    ]
  }}
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
    difficulty_band: str = "neutral",
) -> str:
    """
    Build the prompt used to generate a student exam from a generic source text.

    IMPORTANT:
    - The returned question must already contain blanks / gaps so it can be
      rendered directly in the frontend for the student to complete.
    - The correct answer must be returned separately in the 'answer' field.
    """

    difficulty_instruction = {
        "easier": """
Adaptive difficulty instruction:
- Keep the same Cambridge level.
- Make the exam slightly easier within that level.
- Use clearer wording and more direct clues.
- Prefer more frequent vocabulary.
- Use less misleading distractors.
- Avoid overly tricky transformations.
- Keep items fair, solvable, and confidence-building for the student.
""",
        "neutral": """
Adaptive difficulty instruction:
- Keep the standard difficulty for this Cambridge level.
- Do not intentionally simplify or increase difficulty.
""",
        "harder": """
Adaptive difficulty instruction:
- Keep the same Cambridge level.
- Make the exam slightly harder within that level.
- Use less obvious clues.
- Use stronger distractors.
- Increase paraphrasing difficulty moderately.
- Make transformations less direct, but still fair for the level.
- Keep the exam challenging but fully appropriate for the stated level.
""",
    }.get(
        difficulty_band,
        """
Adaptive difficulty instruction:
- Keep the standard difficulty for this Cambridge level.
- Do not intentionally simplify or increase difficulty.
""",
    )

    return f"""
You are an expert Cambridge English exam designer.

Level: {level}

{difficulty_instruction}

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
- Difficulty must remain appropriate for the stated Cambridge level.
- Apply the adaptive difficulty instruction above only within that same level.
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
- For "Cloze test with options" and "Multiple Choice", each question MUST include the answer options inside the visible question text between parenthesis and separated by a /. For example: Online learning has made education more ____________ (inclusive / exclusive / distant / private).
- Do NOT create an "options" field.
- For "Key word transformation", the visible question must include the sentence with a blank and the key word.
- For "Word Formation", the visible question must include the base word and a blank in the sentence.
- The value of "exercise_type" should match the requested type as closely as possible, but preserving order is more important than exact naming.
- Each exercise block may contain multiple items (no more than three).
- At leat one excercise type must have more than one item.
- Each item must contain exactly one solvable task.
- Each item must require exactly one answer.
- Do not include multiple blanks or multiple things to solve in the same item.
- Do NOT create any extra keys inside an item.
- Each item must contain exactly these keys only:
  - "question"
  - "answer"
- If answer choices are needed, they must be embedded in the "question" text, not stored anywhere else in the JSON.

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
  "question": "Original sentence: After taking a break, he carried on studying. Your sentence: He stopped ____________ (TAKE) and then he carried on studying.",
  "answer": "to take rest"
}}

Multiple Choice Cloze item:
{{
  "question": "Online learning has made education more ____________ (inclusive / exclusive / distant / private)",
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


def build_student_correction_prompt(
    level: str,
    correction_payload: str,
) -> str:
    """
    Build the prompt used to correct a student's submitted exam.
    """

    return f"""
You are an expert Cambridge English examiner.

Level: {level}

You must correct the student's exam attempt using the official answers.

Exam attempt to correct:
{correction_payload}

Mandatory grading policy:
- Evaluate EVERY item individually.
- Be strict. Default to incorrect unless the answer is clearly correct.
- Do not reward vague, guessed, unrelated, contradictory, or overly incomplete answers.
- An empty answer receives 0.0 points.
- A clearly wrong answer receives 0.0 points.
- A partially relevant answer must NEVER receive the same value as a fully correct answer.

Scoring policy per item:
- Use only these values for "awarded_points": 0.0, 0.5, 1.0
- 1.0 = fully correct answer or clearly acceptable equivalent
- 0.5 = only for an answer that is meaningfully close but incomplete or imprecise
- 0.0 = incorrect answer
- For closed or fixed-answer items, use only 0.0 or 1.0
- Use 0.5 only when partial credit is truly deserved
- If you assign 0.5, or assign 1.0 to a non-exact equivalent answer, the item feedback must explicitly explain why

Output policy:
- "feedback" is REQUIRED and non-empty for every exercise
- "feedback" is REQUIRED and non-empty for every item
- "general_feedback" is REQUIRED and non-empty
- The final "score" must be based on the sum of awarded_points divided by the total number of items
- Return STRICT JSON only
- Do not include markdown
- Do not include explanations outside JSON

Required JSON schema:

{{
  "score": 0,
  "general_feedback": "string",
  "exercises": [
    {{
      "exam_exercise_instance_id": 0,
      "exercise_type": "string",
      "correct_count": 0,
      "total_count": 0,
      "awarded_points_sum": 0.0,
      "feedback": "string",
      "items": [
        {{
          "item_index": 0,
          "student_answer": "string",
          "correct_answer": "string",
          "is_correct": false,
          "awarded_points": 0.0,
          "feedback": "string"
        }}
      ]
    }}
  ]
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

def generate_student_correction_from_llm(prompt: str) -> str:
    """
    Call the LLM and return raw correction output text.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        },
        timeout=300,
    )

    response.raise_for_status()

    return response.json()["response"]

def build_writing_feedback_prompt(
    exercise_prompt: str,
    student_submission: str,
) -> str:
    """
    Build the prompt used to review a student's writing submission.

    Output must be strict JSON only.
    Feedback explanations must be in English.
    Corrected writing must remain in English.
    """
    return f"""
You are an expert Cambridge English writing evaluator and teacher.

Your task is to analyze a student's English writing submission and return:
- observations
- corrections
- improvement tips
- an improved corrected version of the text

Important behavior rules:
- Evaluate the student's response against the exercise prompt.
- Be constructive, pedagogical, and specific.
- Do not invent missing student intentions.
- Preserve the student's original meaning when correcting.
- Do not be overly harsh.
- Feedback explanations must be written in English.
- Any corrected writing text must remain in English.
- Output STRICT JSON only.
- Do NOT include markdown.
- Do NOT include explanations outside JSON.

Exercise prompt:
{exercise_prompt}

Student submission:
{student_submission}

Return JSON with this exact schema:

{{
  "overall_assessment": "string",
  "corrected_version": "string",
  "feedback": {{
    "task_achievement": ["string"],
    "grammar": ["string"],
    "vocabulary": ["string"],
    "organization": ["string"]
  }},
  "line_corrections": [
    {{
      "original": "string",
      "corrected": "string",
      "explanation": "string"
    }}
  ],
  "tips": ["string"],
  "estimated_level_fit": "string"
}}

Additional instructions:
- "overall_assessment" should be a short paragraph in English.
- "corrected_version" must be the full corrected version of the student's text in English.
- "feedback" must contain practical observations in English.
- "line_corrections" must include the most important concrete corrections only.
- Include between 3 and 8 items in "line_corrections" when possible.
- "tips" must be actionable and concise, in English.
- "estimated_level_fit" should briefly state whether the writing seems below, aligned with, or above its apparent level.
- If the text is very short, still provide useful feedback.
"""
