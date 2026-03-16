"""
Writing routing module.

Maps HTTP endpoints to the corresponding writing controller functions.
The blueprint defines namespace-only routes; no URL prefix is assigned here,
so each endpoint declares its full public path explicitly.
"""

from flask import Blueprint
from controllers.writing_controller import review_student_writing

writing_bp = Blueprint("writing", __name__)


@writing_bp.route("/api/writing/review", methods=["POST"])
def review_writing():
    """
    Review a student's writing submission with AI.
    ---
    tags:
      - Writing
    summary: Review student writing
    description: >
      Receives a writing exercise prompt and the student's written submission,
      sends both to the AI model, and returns structured feedback with
      observations, corrections, tips, and a corrected version.
      This endpoint does not persist data in the database.

    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - exercise_prompt
              - student_submission
            properties:
              exercise_prompt:
                type: string
                example: "Write an email to a friend telling them about your last holiday."
              student_submission:
                type: string
                example: "Hi John, I am writing to tell you about my holidays..."

    responses:
      200:
        description: Writing feedback generated successfully
      400:
        description: >
          Bad request. Possible messages:
          - Invalid JSON body
          - exercise_prompt is required
          - student_submission is required
          - exercise_prompt exceeds maximum length of N characters
          - student_submission exceeds maximum length of N characters
      401:
        description: Missing or invalid authentication token
      403:
        description: Email not verified
      404:
        description: Student not found
      500:
        description: >
          Internal server error. Possible messages:
          - Model did not return valid JSON
          - Invalid or incomplete writing feedback returned by model
          - Error generating writing feedback
    """
    return review_student_writing()