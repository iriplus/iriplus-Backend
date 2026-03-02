"""Blueprint routes for the Exam entity.

This module defines the HTTP endpoints for CRUD operations on Exam.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required
from controllers.exam_controller import (
    create_exam as controller_create_exam,
    get_all_exams as controller_get_all_exams,
    get_exam_by_id as controller_get_exam_by_id,
    update_exam as controller_update_exam,
    delete_exam as controller_delete_exam,
)
from controllers.exam_generation_controller import generate_exam, get_full_exam, export_exam_pdf, export_exam_docx, refine_exam, get_all_exams_controller, send_exam_to_review, leave_exam_review, accept_exam, send_to_correction
from utils.types_enum import ExamStatus

exam_bp = Blueprint("exam_bp", __name__)


@exam_bp.route("/api/exam", methods=["POST"])
@jwt_required()
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
@jwt_required()
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
    return get_all_exams_controller()


@exam_bp.route("/api/exam/<int:exam_id>", methods=["GET"])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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

@exam_bp.route("/api/exam/generate", methods=["POST"])
@jwt_required()
def generate_exam_route():
    """
    Docstring for generate_exam_route
    """
    return generate_exam()

@exam_bp.route("/api/exam/<int:exam_id>/full", methods=["GET"])
@jwt_required()
def get_exam_full(exam_id: int):
    """
    Docstring for get_exam_full
    
    :param exam_id: Description
    :type exam_id: int
    """
    return get_full_exam(exam_id)


@exam_bp.route("/api/exam/<int:exam_id>/export/pdf", methods=["GET"])
@jwt_required()
def export_exam_pdf_route(exam_id: int):
    """
    Docstring for export_exam_pdf_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return export_exam_pdf(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/refine", methods=["POST"])
@jwt_required()
def refine_exam_route(exam_id: int):
    """
    Docstring for refine_exam_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return refine_exam(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/export/docx", methods=["GET"])
@jwt_required()
def export_exam_docx_route(exam_id: int):
    """
    Docstring for export_exam_docx_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return export_exam_docx(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>", methods=["DELETE"])
@jwt_required()
def delete_exam_route(exam_id: int):
    """
    Docstring for delete_exam_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return delete_exam(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/send-to-review", methods=["PATCH"])
@jwt_required()
def send_to_review_route(exam_id: int):
    """
    Docstring for send_to_review_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return send_exam_to_review(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/leave-review", methods=["PATCH"])
@jwt_required()
def leave_review_route(exam_id: int):
    """
    Docstring for leave_review_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return leave_exam_review(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/accept", methods=["PATCH"])
@jwt_required()
def accept_exam_route(exam_id: int):
    """
    Docstring for accept_exam_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return accept_exam(exam_id)

@exam_bp.route("/api/exam/<int:exam_id>/send-to-correction", methods=["PATCH"])
@jwt_required()
def send_to_correction_route(exam_id: int):
    """
    Docstring for send_to_correction_route
    
    :param exam_id: Description
    :type exam_id: int
    """
    return send_to_correction(exam_id)
