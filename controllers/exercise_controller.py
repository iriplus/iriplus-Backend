"""Controller functions for Exercise entity.

Exposes CRUD-like operations that are typically called from route handlers.
Each function reads request data, interacts with the ORM, and returns a JSON
response with an appropriate HTTP status code.
"""

import datetime
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Exercise
from utils.types_enum import ExerciseArchetype


def _serialize_exercise(exercise: Exercise) -> dict:
    """Serialize an Exercise ORM object to a JSON-safe dict.

    Args:
        exercise: Exercise model instance.

    Returns:
        A dictionary with primitive/JSON-serializable values.
    """
    return {
        "id": exercise.id,
        "archetype": exercise.archetype,
        "content": exercise.content,
        "rubric": exercise.rubric,
        "key": exercise.key,
        "date_created": exercise.date_created.isoformat() if exercise.date_created else None,
        "exam": {
            "id": exercise.exam.id,
        }
    }


def create_exercise(exercise_archetype: str):
    """Create an Exercise record from the JSON request body.

    Expected JSON fields:
        - archetype (str)
        - content (text)
        - rubric (str)
        - key (int)
        - exam_id (int)
    
    Returns:
        JSON payload with the new resource id on success, or an error message.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        archetype_enum = ExerciseArchetype[exercise_archetype.upper()]
        content = data["content"]
        rubric = data["rubric"]
        key = data["key"]
        exam_id = data["exam_id"]

        new_exercise = Exercise(
            archetype=archetype_enum,
            content=content,
            rubric=rubric,
            key=key,
            exam_id=exam_id,
            date_created=datetime.datetime.now(),
        )

        db.session.add(new_exercise)
        db.session.commit()

        return jsonify(
            {"message": "Exercise created successfully", "id": new_exercise.id}
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


def get_all_exercises():
    """Return all non-deleted exercises as a JSON array."""
    try:
        exercises = Exercise.query.filter_by(date_deleted=None).all()
        result = [_serialize_exercise(exercise) for exercise in exercises]
        return jsonify(result), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_exercise_by_id(exercise_id: int):
    """Return a single Exercise by id if it exists and is not soft-deleted.

    Args:
        exercise_id: Primary key of the Exercise.

    Returns:
        JSON object with the exercise data or a 404 error if not found.
    """
    try:
        exercise = Exercise.query.get(exercise_id)
        if not exercise or exercise.date_deleted:
            return jsonify({"message": "Exercise not found"}), 404

        return jsonify(_serialize_exercise(exercise)), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def update_exercise(exercise_id: int):
    """Update mutable fields of an existing Exercise.

    Args:
        exercise_id: Primary key of the Exercise to update.

    Returns:
        JSON with a success message or an error status/message.
    """
    exercise = Exercise.query.get(exercise_id)
    if not exercise or exercise.date_deleted:
        return jsonify({"message": "Exercise not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        # Only overwrite fields present in the payload; keep current values otherwise.
        exercise.archetype = data.get("archetype", exercise.archetype)
        exercise.content = data.get("content", exercise.content)
        exercise.rubric = data.get("rubric", exercise.rubric)
        exercise.key = data.get("key", exercise.key)

        db.session.commit()
        return jsonify({"message": "Exercise updated successfully"}), 200

    except (TypeError, ValueError) as err:
        db.session.rollback()
        return jsonify({"message": f"Invalid field value: {err}"}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def delete_exercise(exercise_id: int):
    """Soft-delete an Exercise by setting the date_deleted timestamp.

    Args:
        exercise_id: Primary key of the Exercise to soft-delete.

    Returns:
        JSON with a success message, or 404 if the class does not exist.
    """
    exercise = Exercise.query.get(exercise_id)
    if not exercise or exercise.date_deleted:
        return jsonify({"message": "Exercise not found"}), 404

    try:
        # Soft delete by timestamp; keep record for audit and FK integrity.
        exercise.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message": "Exercise deleted successfully"}), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500
