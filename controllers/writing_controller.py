import json
from typing import Any

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from orm_models import User, db
from services.llm_service import build_writing_feedback_prompt, generate_exam_from_llm
from controllers.exam_generation_controller import extract_json


MAX_PROMPT_LENGTH = 4000
MAX_SUBMISSION_LENGTH = 6000


def _validate_writing_feedback_response(data: dict[str, Any]) -> str | None:
    """
    Validate the top-level structure returned by the model.
    Returns an error message if invalid, otherwise None.
    """
    required_string_fields = [
        "overall_assessment",
        "corrected_version",
        "estimated_level_fit",
    ]

    for field in required_string_fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"Invalid or missing field: {field}"

    feedback = data.get("feedback")
    if not isinstance(feedback, dict):
        return "Invalid or missing field: feedback"

    feedback_keys = [
        "task_achievement",
        "grammar",
        "vocabulary",
        "organization",
    ]

    for key in feedback_keys:
        value = feedback.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            return f"Invalid feedback section: {key}"

    line_corrections = data.get("line_corrections")
    if not isinstance(line_corrections, list):
        return "Invalid or missing field: line_corrections"

    for item in line_corrections:
        if not isinstance(item, dict):
            return "Invalid item in line_corrections"

        original = item.get("original")
        corrected = item.get("corrected")
        explanation = item.get("explanation")

        if not isinstance(original, str) or not original.strip():
            return "Invalid line_corrections.original"

        if not isinstance(corrected, str) or not corrected.strip():
            return "Invalid line_corrections.corrected"

        if not isinstance(explanation, str) or not explanation.strip():
            return "Invalid line_corrections.explanation"

    tips = data.get("tips")
    if not isinstance(tips, list) or not all(
        isinstance(item, str) and item.strip() for item in tips
    ):
        return "Invalid or missing field: tips"

    return None

@jwt_required()
def review_student_writing():
    """
    Generate AI feedback for a student's writing submission without persistence.

    Expected JSON payload:
    {
        "exercise_prompt": str,
        "student_submission": str
    }

    Returns:
        200 with structured writing feedback if successful.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    exercise_prompt = data.get("exercise_prompt")
    student_submission = data.get("student_submission")

    if not isinstance(exercise_prompt, str) or not exercise_prompt.strip():
        return jsonify({"message": "exercise_prompt is required"}), 400

    if not isinstance(student_submission, str) or not student_submission.strip():
        return jsonify({"message": "student_submission is required"}), 400

    exercise_prompt = exercise_prompt.strip()
    student_submission = student_submission.strip()

    if len(exercise_prompt) > MAX_PROMPT_LENGTH:
        return jsonify({
            "message": f"exercise_prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
        }), 400

    if len(student_submission) > MAX_SUBMISSION_LENGTH:
        return jsonify({
            "message": f"student_submission exceeds maximum length of {MAX_SUBMISSION_LENGTH} characters"
        }), 400

    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user or user.date_deleted is not None:
        return jsonify({"message": "Student not found"}), 404

    if user.is_verified is not True:
        return jsonify({"message": "Email not verified"}), 403

    try:
        prompt = build_writing_feedback_prompt(
            exercise_prompt=exercise_prompt,
            student_submission=student_submission,
        )

        raw_output = generate_exam_from_llm(prompt)

        try:
            cleaned_json = extract_json(raw_output)
            parsed_output: dict[str, Any] = json.loads(cleaned_json)
        except Exception:
            return jsonify({"message": "Model did not return valid JSON"}), 500

        validation_error = _validate_writing_feedback_response(parsed_output)
        if validation_error is not None:
            return jsonify({"message": validation_error}), 500

        return jsonify({
            "message": "Writing feedback generated successfully",
            "result": parsed_output,
        }), 200

    except Exception as exc:
        print(f"Error generating writing feedback: {exc}")
        return jsonify({"message": "Error generating writing feedback"}), 500