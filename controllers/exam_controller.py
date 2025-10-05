"""Controller functions for Exam entity.

Exposes CRUD-like operations that are typically called from route handlers.
Each function reads request data, interacts with the ORM, and returns a JSON
response with an appropriate HTTP status code.
"""

import datetime
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Exam


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
    }


def create_exam():
    """Create an Exam record from the JSON request body.

    Returns:
        JSON payload with the new resource id on success, or an error message.
    """
    #data = request.get_json(silent=True)
    #if not data:
    #    return jsonify({"message": "Invalid JSON body"}), 400

    try:
        status = "Pending review"

        new_exam = Exam(
            status=status,
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
        # Only overwrite fields present in the payload; keep current values otherwise.
        exam.status = data.get("status", exam.status)
        exam.notes = data.get("notes", exam.notes)

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
