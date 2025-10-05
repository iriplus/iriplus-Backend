"""Controller logic for Level entity.

This module contains the business logic for creating and managing Level
records. Controllers sit between routes (HTTP layer) and models (ORM layer).
"""

import datetime
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Level


def _serialize_level(level: Level) -> dict:
    """Serialize a Level ORM object to a JSON-safe dict.

    Args:
        level: Level model instance.

    Returns:
        A dictionary with primitive/JSON-serializable values.
    """
    return {
        "id": level.id,
        "description": level.description,
        "cosmetic": level.cosmetic,
        "min_xp": level.min_xp,
        "date_created": level.date_created.isoformat() if level.date_created else None,
    }

def create_level():
    """Create a new Level from JSON request payload.

    Expects JSON with:
        - description (str): description of the level.
        - cosmetic (str): optional cosmetic metadata.
        - min_xp (int): minimum XP required for this level.

    Returns:
        JSON response with a success message and new Level ID,
        or an error response with appropriate HTTP status code.
    """
    # Parse JSON body; return error if missing/invalid.
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        # Extract required fields from request payload.
        description = data["description"]
        cosmetic = data["cosmetic"]
        min_xp = data["min_xp"]

        # Create Level instance with current timestamp.
        level = Level(
            description=description,
            cosmetic=cosmetic,
            min_xp=min_xp,
            date_created=datetime.datetime.now(),
        )

        # Persist new record in database.
        db.session.add(level)
        db.session.commit()

        return jsonify(
            {"message": "Level created successfully", "id": level.id}
        ), 201

    except Exception as e:  # pylint: disable=broad-except
        # Catch-all for unexpected errors (log in production).
        return jsonify(
            {"message": f"Something went wrong: {e}"}
        ), 501

def get_all_levels():
    """Return all non-deleted levels as a JSON array."""
    try:
        levels = Level.query.filter_by(date_deleted=None).all()
        result = [_serialize_level(level) for level in levels]
        return jsonify(result), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500

def get_level_by_id(level_id: int):
    """Return a single level by id if it exists and is not soft-deleted.

    Args:
        level_id: Primary key of the level.

    Returns:
        JSON object with the level data or a 404 error if not found.
    """
    try:
        level = Level.query.get(level_id)
        if not level or level.date_deleted:
            return jsonify({"message": "level not found"}), 404
        return jsonify(_serialize_level(level)), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500

def update_level(level_id: int):
    """Update mutable fields of an existing Level.

    Args:
        level_id: Primary key of the Level to update.

    Returns:
        JSON with a success message or an error status/message.
    """
    level = Level.query.get(level_id)
    if not level or level.date_deleted:
        return jsonify({"message": "Level not found"},404)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400
    try:
        level.description = data.get("description", level.description)
        level.cosmetic = data.get("cosmetic", level.cosmetic)
        level.min_xp = int(data.get("min_xp", level.min_xp))
        db.session.commit()
        return jsonify ({"message": f"Level {level.id} updated succesfully"}, 200)
    except (TypeError, ValueError) as err:
        db.session.rollback()
        return jsonify({"message": f"Invalid field value: {err}"}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500

def soft_delete_level(level_id:int):
    """Soft-delete a Level by setting the date_deleted timestamp.

    Args:
        level_id: Primary key of the Level to soft-delete.

    Returns:
        JSON with a success message, or 404 if the Level does not exist.
    """
    level = Level.query.get(level_id)
    if not level or level.date_deleted:
        return jsonify({"message":"Level not found"}), 404
    try:
        level.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message":f"Level {level.id} deleted successfully"}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500

def hard_delete_level(level_id:int):
    """Hard-delete a Level.

    Args:
        level_id: Primary key of the Level to hard-delete.

    Returns:
        JSON with a success message, or 404 if the Level does not exist.
    """
    level = Level.query.get(level_id)
    if not level or level.date_deleted:
        return jsonify({"message":"Level not found"}), 404
    try:
        db.session.delete(level)
        db.session.commit()
        return jsonify({"message":f"Level {level.id} deleted successfully"}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500
