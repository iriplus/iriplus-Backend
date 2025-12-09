"""Blueprint routes for the Exam entity.

This module defines the HTTP endpoints for CRUD operations on Exam.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint
from controllers.exam_controller import (
    create_exam as controller_create_exam,
    get_all_exams as controller_get_all_exams,
    get_exam_by_id as controller_get_exam_by_id,
    update_exam as controller_update_exam,
    delete_exam as controller_delete_exam,
)
from utils.types_enum import ExamStatus

exam_bp = Blueprint("exam_bp", __name__)


@exam_bp.route("/api/exam", methods=["POST"])
def create_exam():
    """
    Create a new Exam
    ---
    tags:
      - Exam
    summary: Create a new Exam
    description: Create a new Exam entity for a given class. Status is set automatically to TEST_EXAM.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExamInput'
    responses:
      201:
        description: Exam created
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Exam'
      400:
        description: Invalid input payload
      500:
        description: Server error
    """
    return controller_create_exam(exam_status=ExamStatus.TEST_EXAM)


@exam_bp.route("/api/exam", methods=["GET"])
def get_all_exams():
    """
    List all Exams
    ---
    tags:
      - Exam
    summary: List all Exams
    description: Retrieve all Exams that have not been soft-deleted.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Exam'
      500:
        description: Server error
    """
    return controller_get_all_exams()


@exam_bp.route("/api/exam/<int:exam_id>", methods=["GET"])
def get_exam_by_id(exam_id: int):
    """
    Get an Exam by ID
    ---
    tags:
      - Exam
    summary: Retrieve an Exam
    description: Get an Exam by its ID.
    parameters:
      - in: path
        name: exam_id
        schema:
          type: integer
        required: true
        description: Primary key of the Exam
    responses:
      200:
        description: Exam found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Exam'
      404:
        description: Exam not found
      500:
        description: Server error
    """
    return controller_get_exam_by_id(exam_id)


@exam_bp.route("/api/exam/<int:exam_id>", methods=["PUT"])
def update_exam(exam_id: int):
    """
    Update an Exam
    ---
    tags:
      - Exam
    summary: Update an existing Exam
    description: Update fields for an existing Exam entity.
    parameters:
      - in: path
        name: exam_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExamInput'
    responses:
      200:
        description: Exam updated
      400:
        description: Invalid input payload
      404:
        description: Exam not found
      500:
        description: Server error
    """
    return controller_update_exam(exam_id)


@exam_bp.route("/api/exam/<int:exam_id>", methods=["DELETE"])
def delete_exam(exam_id: int):
    """
    Soft delete an Exam
    ---
    tags:
      - Exam
    summary: Soft delete an Exam
    description: Perform a soft delete of an Exam by setting date_deleted.
    parameters:
      - in: path
        name: exam_id
        schema:
          type: integer
        required: true
    responses:
      200:
        description: Exam deleted
      404:
        description: Exam not found
      500:
        description: Server error
    """
    return controller_delete_exam(exam_id)
