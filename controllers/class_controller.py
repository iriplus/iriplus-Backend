"""Controller functions for Class entity.

Exposes CRUD-like operations that are typically called from route handlers.
Each function reads request data, interacts with the ORM, and returns a JSON
response with an appropriate HTTP status code.
"""

import uuid
import datetime
from flask import request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Class

# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def generate_class_code() -> str:
    """Generate an 8-char uppercase unique code derived from UUID4."""
    return uuid.uuid4().hex[:8].upper()

def _serialize_class(clazz: Class) -> dict:
    """Serialize a Class ORM object to a JSON-safe dict.

    Args:
        clazz: Class model instance.

    Returns:
        A dictionary with primitive/JSON-serializable values.
    """
    return {
        "id": clazz.id,
        "class_code": clazz.class_code,
        "description": clazz.description,
        "suggested_level": clazz.suggested_level,
        "max_capacity": clazz.max_capacity,
        "date_created": clazz.date_created.isoformat() if clazz.date_created else None,
    }


def create_class():
    """Create a Class record from the JSON request body.

    Expected JSON fields:
        - description (str)
        - suggested_level (str)
        - max_capacity (int)

    Returns:
        JSON payload with the new resource id on success, or an error message.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        description = data["description"]
        suggested_level = data["suggested_level"]
        max_capacity = int(data["max_capacity"])

        new_class = Class(
            description=description,
            suggested_level=suggested_level,
            max_capacity=max_capacity,
            class_code=generate_class_code(),
            date_created=datetime.datetime.now(),
        )

        db.session.add(new_class)
        db.session.commit()

        return jsonify(
            {"message": "Class created successfully", "class_code": new_class.class_code, "id": new_class.id}
        ), 201

    except KeyError as e:
        # Missing required field in the payload.
        return jsonify({"message": f"Missing required field: {e}"}), 400
    except (TypeError, ValueError) as e:
        # Invalid types (e.g., non-numeric max_capacity).
        return jsonify({"message": f"Invalid field value: {e}"}), 400
    except SQLAlchemyError as e:
        # Database/transaction error (log 'err' detail in real apps).
        db.session.rollback()
        return jsonify({"message": f"Database error: {e}"}), 500
    except Exception as e:  # pylint: disable=broad-except
        # Catch-all for unexpected errors.
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {e}"}), 500


def get_all_classes():
    """Return all non-deleted classes as a JSON array."""
    try:
        classes = Class.query.filter_by(date_deleted=None).all()
        result = [_serialize_class(clazz) for clazz in classes]
        return jsonify(result), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def get_class_by_id(class_id: int):
    """Return a single Class by id if it exists and is not soft-deleted.

    Args:
        class_id: Primary key of the Class.

    Returns:
        JSON object with the class data or a 404 error if not found.
    """
    try:
        clazz = Class.query.get(class_id)
        if not clazz or clazz.date_deleted:
            return jsonify({"message": "Class not found"}), 404

        return jsonify(_serialize_class(clazz)), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500

def get_class_by_class_code(class_code: str):
    """Return a single Class by class_code if it exists and is not soft-deleted.

    Args:
        class_code: Unique code of the Class.

    Returns:
        JSON object with the class data or a 404 error if not found.
    """
    try:
        normalized = class_code.strip().upper()

        clazz = Class.query.filter(func.trim(Class.class_code) == normalized).first()
        if not clazz or clazz.date_deleted:
            return jsonify({"message": "Class not found"}), 404

        return jsonify(_serialize_class(clazz)), 200
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"message": f"Something went wrong: {err}"}), 500

def update_class(class_id: int):
    """Update mutable fields of an existing Class.

    Args:
        class_id: Primary key of the Class to update.

    Returns:
        JSON with a success message or an error status/message.
    """
    clazz = Class.query.get(class_id)
    if not clazz or clazz.date_deleted:
        return jsonify({"message": "Class not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        clazz.description = data.get("description", clazz.description)
        clazz.suggested_level = data.get("suggested_level", clazz.suggested_level)

        if "max_capacity" in data:
            clazz.max_capacity = int(data["max_capacity"])

        db.session.commit()
        return jsonify({"message": "Class updated successfully"}), 200

    except (TypeError, ValueError) as err:
        db.session.rollback()
        return jsonify({"message": f"Invalid field value: {err}"}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Something went wrong: {err}"}), 500


def delete_class(class_id: int):
    """Soft-delete a Class by setting the date_deleted timestamp.

    Args:
        class_id: Primary key of the Class to soft-delete.

    Returns:
        JSON with a success message, or 404 if the class does not exist.
    """
    clazz = Class.query.get(class_id)
    if not clazz or clazz.date_deleted:
        return jsonify({"message": "Class not found"}), 404

    try:
        # Soft delete by timestamp; keep record for audit and FK integrity.
        clazz.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message": "Class deleted successfully"}), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500
