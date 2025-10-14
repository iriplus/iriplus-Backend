"""Controller functions for Exam entity.

Exposes CRUD-like operations that are typically called from route handlers.
Each function reads request data, interacts with the ORM, and returns a JSON
response with an appropriate HTTP status code.
"""

import datetime
from typing import cast, List
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Exam, User, Class, Exercise
from utils.types_enum import UserType, ExamStatus


def _serialize_exam(exam: Exam) -> dict:
    """Serialize an Exam ORM object to a JSON-safe dict.

    Args:
        exam: Exam model instance.

    Returns:
        A dictionary with primitive/JSON-serializable values.
    """
    return {
        "id": exam.id,
        "status": exam.status,
        "notes": exam.notes,
        "date_created": exam.date_created.isoformat() if exam.date_created else None,
        "class": (
            {
                "id": exam.class_exam.id,
                "description": exam.class_exam.description,
            } if exam.class_exam else None
        ),
        "coordinator_id": (
            {
                "id": exam.coordinator_exam.id,
                "name": exam.coordinator_exam.name,
                "surname": exam.coordinator_exam.surname,
        } if exam.coordinator_exam else None
        ),
        "student": (
            {
                "id": exam.student_exam.id,
                "name": exam.student_exam.name,
                "surname": exam.student_exam.surname,
        } if exam.student_exam else None
        ),
        "exercises": [
            {"id": exercise.id, "archetype": exercise.archetype, "key": exercise.key}
            for exercise in cast(List[Exercise], exam.exercises)
        ],
    }


def create_exam(exam_status: str):
    """Create an Exam record from the JSON request body.

    Expected JSON fields:
        - status (required)
        - notes (optional)
        - coordinator_id (optional)
        - student_id (optional)
        - class_id (optional)
    
    Returns:
        JSON payload with the new resource id on success, or an error message.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        exam_enum = ExamStatus[exam_status.upper()]
        notes = "Empty notes"

        coordinator_id = data.get("coordinator_id")
        student_id = data.get("student_id")
        class_id = data.get("class_id")

        # --- Validate relationships ---
        if coordinator_id:
            coordinator = User.query.get(coordinator_id)
            if not coordinator or coordinator.type not in [UserType.COORDINATOR]:
                return jsonify({"message": "Coordinator must be a COORDINATOR"}), 400

        if student_id:
            student = User.query.get(student_id)
            if not student or student.type != UserType.STUDENT:
                return jsonify({"message": "Student must be of type STUDENT."}), 400

        if class_id:
            class_obj = Class.query.get(class_id)
            if not class_obj or class_obj.date_deleted:
                return jsonify({"message": "Class not found or deleted."}), 404


        new_exam = Exam(
            status=exam_enum,
            notes=notes,
            coordinator_id=coordinator_id,
            student_id=student_id,
            class_id=class_id,
            date_created=datetime.datetime.now(),
        )

        db.session.add(new_exam)
        db.session.commit()

        return jsonify(
            {"message": "Exam created successfully", "id": new_exam.id}
        ), 201

    except KeyError as err:
        # Missing required field in the payload.
        return jsonify({"message": f"Missing required field: {err}"}), 400
    except (TypeError, ValueError) as err:
        # Invalid types (e.g., non-numeric max_capacity).
        return jsonify({"message": f"Invalid field value: {err}"}), 400
    except SQLAlchemyError as err:
        # Database/transaction error (log 'err' detail in real apps).
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        # Catch-all for unexpected errors.
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_all_exams():
    """Return all non-deleted exams as a JSON array."""
    try:
        exams = Exam.query.filter_by(date_deleted=None).all()
        result = [_serialize_exam(exam) for exam in exams]
        return jsonify(result), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_exam_by_id(exam_id: int):
    """Return a single Exam by id if it exists and is not soft-deleted.

    Args:
        exam_id: Primary key of the Exam.

    Returns:
        JSON object with the exam data or a 404 error if not found.
    """
    try:
        exam = Exam.query.get(exam_id)
        if not exam or exam.date_deleted:
            return jsonify({"message": "Exam not found"}), 404

        return jsonify(_serialize_exam(exam)), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def update_exam(exam_id: int):
    """Update mutable fields of an existing Exam.

    Args:
        exam_id: Primary key of the Exam to update.

    Returns:
        JSON with a success message or an error status/message.
    """
    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        # Update base fields
        exam.status = data.get("status", exam.status)
        exam.notes = data.get("notes", exam.notes)

        # Update relationships if provided
        if data.get("coordinator_id"):
            coordinator = User.query.get(data["coordinator_id"])
            if not coordinator or coordinator.type not in [UserType.COORDINATOR, UserType.TEACHER]:
                return jsonify({"message": "Invalid coordinator type"}), 400
            exam.coordinator_id = data["coordinator_id"]

        if data.get("student_id"):
            student = User.query.get(data["student_id"])
            if not student or student.type != UserType.STUDENT:
                return jsonify({"message": "Invalid student type"}), 400
            exam.student_id = data["student_id"]

        if data.get("class_id"):
            class_obj = Class.query.get(data["class_id"])
            if not class_obj or class_obj.date_deleted:
                return jsonify({"message": "Class not found or deleted"}), 404
            exam.class_id = data["class_id"]

        db.session.commit()
        return jsonify({"message": "Exam updated successfully"}), 200

    except (TypeError, ValueError) as err:
        db.session.rollback()
        return jsonify({"message": f"Invalid field value: {err}"}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def delete_exam(exam_id: int):
    """Soft-delete an Exam by setting the date_deleted timestamp.

    Args:
        exam_id: Primary key of the Exam to soft-delete.

    Returns:
        JSON with a success message, or 404 if the class does not exist.
    """
    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404

    try:
        # Soft delete by timestamp; keep record for audit and FK integrity.
        exam.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message": "Exam deleted successfully"}), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500
