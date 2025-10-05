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

# Create a Blueprint for Exam-related routes.
exam_bp = Blueprint("exam_bp", __name__)


@exam_bp.route("/api/exam", methods=["POST"])
def create_exam():
    """HTTP POST endpoint to create a new exam."""
    return controller_create_exam()


@exam_bp.route("/api/exam", methods=["GET"])
def get_all_exams():
    """HTTP GET endpoint to retrieve all Exams."""
    return controller_get_all_exams()


@exam_bp.route("/api/exam/<int:exam_id>", methods=["GET"])
def get_exam_by_id(exam_id: int):
    """HTTP GET endpoint to retrieve a Exam by its ID.

    Args:
        exam_id: Primary key of the Exam to retrieve.
    """
    return controller_get_exam_by_id(exam_id)


@exam_bp.route("/api/exam/<int:exam_id>", methods=["PUT"])
def update_exam(exam_id: int):
    """HTTP PUT endpoint to update an existing Exam.

    Args:
        exam_id: Primary key of the Exam to update.
    """
    return controller_update_exam(exam_id)


@exam_bp.route("/api/exam/<int:exam_id>", methods=["DELETE"])
def delete_exam(exam_id: int):
    """HTTP DELETE endpoint to soft-delete a Exam.

    Args:
        exam_id: Primary key of the Exam to delete.
    """
    return controller_delete_exam(exam_id)
