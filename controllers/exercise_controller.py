"""Controller logic for Exercise entity.

This module contains the business logic for creating, reading, updating,
and soft-deleting Exercise records.

Important:
    In this application, Exercise represents an exercise type/archetype
    that can later be reused in exam generation workflows. It does not
    represent a concrete generated question instance.
"""

import datetime
from typing import Any

from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from orm_models import Exercise, db


def _serialize_exercise(exercise: Exercise) -> dict[str, Any]:
    """Serialize an Exercise ORM object into a JSON-safe dictionary.

    Args:
        exercise: Exercise model instance.

    Returns:
        Dictionary with primitive values ready to be returned as JSON.
    """
    return {
        "id": exercise.id,
        "name": exercise.name,
        "content_description": exercise.content_description,
        "date_created": (
            exercise.date_created.isoformat()
            if exercise.date_created is not None
            else None
        ),
    }


def _validate_string_field(value: Any, field_name: str) -> str:
    """Validate that a payload field is a non-empty string.

    Args:
        value: Raw field value extracted from the request JSON body.
        field_name: Human-readable field name used in error messages.

    Returns:
        The normalized trimmed string value.

    Raises:
        ValueError: If the value is not a valid non-empty string.
    """
    if not isinstance(value, str):
        raise ValueError(f"Field '{field_name}' must be a string.")

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(f"Field '{field_name}' is required.")

    return normalized_value


def _validate_exercise_payload(data: dict[str, Any]) -> tuple[str, str]:
    """Validate and normalize Exercise payload data.

    Expected payload:
        {
            "name": "<string>",
            "content_description": "<string>"
        }

    Args:
        data: Parsed JSON request body.

    Returns:
        Tuple containing normalized (name, content_description).

    Raises:
        ValueError: If one or more fields are invalid.
    """
    name = _validate_string_field(data.get("name"), "name")
    content_description = _validate_string_field(
        data.get("content_description"),
        "content_description",
    )

    if len(name) > 255:
        raise ValueError("Field 'name' must not exceed 255 characters.")

    return name, content_description


def _find_exercise_by_name(name: str) -> Exercise | None:
    """Find an Exercise by name using a case-insensitive lookup.

    Args:
        name: Exercise type name to search for.

    Returns:
        Matching Exercise instance if found, otherwise None.
    """
    return (
        db.session.query(Exercise)
        .filter(func.lower(Exercise.name) == name.lower())
        .first()
    )


def create_exercise():
    """Create a new Exercise type from the JSON request body.

    Returns:
        201 with the created Exercise payload on success.
        400 if the JSON body or fields are invalid.
        409 if the name already exists.
        500 if an unexpected database/server error occurs.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        name, content_description = _validate_exercise_payload(data)

        existing_exercise = _find_exercise_by_name(name)
        if existing_exercise is not None:
            if existing_exercise.date_deleted is None:
                return jsonify({
                    "message": "An active exercise type with this name already exists."
                }), 409

            return jsonify({
                "message": (
                    "An exercise type with this name already exists but was "
                    "previously deleted. Reusing the same name is not allowed "
                    "with the current database constraint."
                )
            }), 409

        exercise = Exercise(
            name=name,
            content_description=content_description,
        )

        db.session.add(exercise)
        db.session.commit()

        return jsonify(_serialize_exercise(exercise)), 201

    except ValueError as err:
        return jsonify({"message": str(err)}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_all_exercises():
    """Return all active Exercise types.

    Active means records whose ``date_deleted`` is None.

    Returns:
        200 with a JSON array of active Exercise types.
        500 if a database/server error occurs.
    """
    try:
        exercises = (
            db.session.query(Exercise)
            .filter(Exercise.date_deleted.is_(None))
            .order_by(Exercise.date_created.desc(), Exercise.id.desc())
            .all()
        )

        result = [_serialize_exercise(exercise) for exercise in exercises]
        return jsonify(result), 200

    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_exercise_by_id(exercise_id: int):
    """Return a single active Exercise by its identifier.

    Args:
        exercise_id: Primary key of the Exercise.

    Returns:
        200 with the Exercise payload if found and active.
        404 if the Exercise does not exist or was soft-deleted.
        500 if a database/server error occurs.
    """
    try:
        exercise = db.session.get(Exercise, exercise_id)

        if exercise is None or exercise.date_deleted is not None:
            return jsonify({"message": "Exercise type not found"}), 404

        return jsonify(_serialize_exercise(exercise)), 200

    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def update_exercise(exercise_id: int):
    """Update mutable fields of an existing active Exercise.

    Args:
        exercise_id: Primary key of the Exercise to update.

    Returns:
        200 with the updated Exercise payload on success.
        400 if the JSON body or fields are invalid.
        404 if the Exercise does not exist or was soft-deleted.
        409 if the requested new name already exists.
        500 if a database/server error occurs.
    """
    exercise = db.session.get(Exercise, exercise_id)

    if exercise is None or exercise.date_deleted is not None:
        return jsonify({"message": "Exercise type not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        merged_payload = {
            "name": data.get("name", exercise.name),
            "content_description": data.get(
                "content_description",
                exercise.content_description,
            ),
        }

        name, content_description = _validate_exercise_payload(merged_payload)

        existing_exercise = _find_exercise_by_name(name)
        if existing_exercise is not None and existing_exercise.id != exercise.id:
            if existing_exercise.date_deleted is None:
                return jsonify({
                    "message": "An active exercise type with this name already exists."
                }), 409

            return jsonify({
                "message": (
                    "An exercise type with this name already exists but was "
                    "previously deleted. Reusing the same name is not allowed "
                    "with the current database constraint."
                )
            }), 409

        exercise.name = name
        exercise.content_description = content_description

        db.session.commit()

        return jsonify(_serialize_exercise(exercise)), 200

    except ValueError as err:
        db.session.rollback()
        return jsonify({"message": str(err)}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def soft_delete_exercise(exercise_id: int):
    """Soft-delete an Exercise by setting ``date_deleted``.

    Args:
        exercise_id: Primary key of the Exercise to soft-delete.

    Returns:
        200 with a success message on success.
        404 if the Exercise does not exist or was already deleted.
        500 if a database/server error occurs.
    """
    exercise = db.session.get(Exercise, exercise_id)

    if exercise is None or exercise.date_deleted is not None:
        return jsonify({"message": "Exercise type not found"}), 404

    try:
        exercise.date_deleted = datetime.datetime.now()
        db.session.commit()

        return jsonify({
            "message": f"Exercise type {exercise.id} deleted successfully"
        }), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500
