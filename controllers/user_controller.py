"""Controller logic for user management.

This module defines the CRUD operations for User entities.
It provides endpoints for creating, retrieving, updating, and deleting users,
including type-specific filtering for Students, Teachers, and Coordinators.
"""

import bcrypt
from flask import request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, User, Class
from utils.types_enum import UserType
from utils.email_utils import send_welcome_email
from utils.token_utils import generate_verification_token


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def serialize_user(user: User) -> dict:
    """Serialize a User ORM instance into a JSON-compatible dictionary.

    Args:
        user: SQLAlchemy User model instance.

    Returns:
        A dictionary containing serializable user attributes.
    """
    return {
        "id": user.id,
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "dni": user.dni,
        "profile_picture": user.profile_picture,
        "type": user.type.value if user.type else None,
        "accumulated_xp": user.accumulated_xp,
        "student_level_id": user.student_level_id,
        "student_class_id": user.student_class_id,
        "is_verified": user.is_verified
    }

# ---------------------------------------------------------------------------
# Controller functions
# ---------------------------------------------------------------------------

def create_user(user_type: UserType):
    """Create a new user of a given type (Student, Teacher, Coordinator).

    Args:
        user_type: String representation of the user type to assign.

    Returns:
        JSON response containing the new user data or an error message.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body."}), 400
    # Validate required fields.
    required_fields = ["name", "surname", "email", "passwd", "dni"]
    if user_type == UserType.STUDENT:
        required_fields.append("student_class_id")
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    try:

        # Hash the provided password using bcrypt with salt.
        hashed_password = bcrypt.hashpw(
            data["passwd"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Create new user instance.
        new_user = User(
            name=data["name"],
            surname=data["surname"],
            email=data["email"].lower(),
            passwd=hashed_password,
            dni=data["dni"],
            type=user_type,
            accumulated_xp=data.get("accumulated_xp", 0),
            profile_picture=data.get("profile_picture"),
            student_level_id=data.get("student_level_id"),
            student_class_id=data.get("student_class_id"),
        )

        # Commit transaction.
        db.session.add(new_user)
        db.session.commit()
        token = generate_verification_token(new_user.email)
        send_welcome_email(new_user.email, new_user.name, token)

        return jsonify({
            "message": "User created successfully. Verification email sent.",
            "user": serialize_user(new_user)
        }), 201

    except KeyError:
        # Handle invalid user type string.
        return jsonify({"message": f"Invalid user type: {user_type}"}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500

def register_student():
    """Create a new Student user.

    Validates:
    - Required fields
    - Email uniqueness
    - DNI uniqueness
    - Class existence
    - Class capacity
    - Soft delete constraints

    Returns:
        201 Created on success
        400 Bad request for invalid input
        404 Class not found
        409 Email or DNI already exists
        422 Class is full
    """

    data = request.get_json(silent=True) or {}

    required_fields = ["name", "surname", "email", "passwd", "dni", "class_code"]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({
            "message": f"Missing required fields: {', '.join(missing)}"}), 400
    name = data["name"].strip()
    surname = data["surname"].strip()
    email = data["email"].strip().lower()
    passwd = data["passwd"]
    dni = data["dni"].strip()
    class_code = data["class_code"].strip()

    try:
        # Check for existing email or DNI
        existing_email = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if existing_email and not existing_email.date_deleted:
            return jsonify({"message": "Email already exists."}), 409
        existing_dni = User.query.filter(
            func.trim(User.dni) == dni
        ).first()

        if existing_dni and not existing_dni.date_deleted:
            return jsonify({"message": "DNI already exists."}), 409

        # Verify class existence and capacity
        clazz = Class.query.filter(
            func.trim(Class.class_code) == class_code,
            Class.date_deleted.is_(None),
        ).first()

        if not clazz:
            return jsonify({"message": "Class not found."}), 404
        current_students = (
            db.session.query(func.count(User.id)) # pylint: disable=not-callable
            .filter(
                User.student_class_id == clazz.id,
                User.date_deleted.is_(None),
            ).scalar()
        )

        print(current_students, clazz.max_capacity)

        if current_students >= clazz.max_capacity:
            return jsonify({"message": "Class is full."}), 422
        # Hash password
        hashed_password = bcrypt.hashpw(
            passwd.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Create new student user
        new_user = User(
            name=name,
            surname=surname,
            email=email,
            passwd=hashed_password,
            dni=dni,
            type=UserType.STUDENT,
            student_class_id=clazz.id,
            accumulated_xp=0,
            is_verified=False
        )

        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        token = generate_verification_token(new_user.email)
        send_welcome_email(new_user.email, new_user.name, token)

        return jsonify({
            "message": "Student created successfully. Verification email sent."
        }), 201
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500

def get_user(user_id: int):
    """Retrieve a single user by ID.

    Args:
        user_id: Primary key of the user to fetch.

    Returns:
        JSON response containing user data or a 404 message.
    """
    user = User.query.get(user_id)
    if not user or user.date_deleted:
        return jsonify({"message": "User not found."}), 404

    return jsonify(serialize_user(user)), 200

def get_user_by_email(user_email: str):
    """Retrieve a single user by email.

    Args:
        email: Email address of the user to fetch.
    Returns:
        JSON response containing user data or a 404 message.
    """

    normalized_email = user_email.strip().lower()

    user = User.query.filter(User.email == normalized_email).first()
    if not user or user.date_deleted:
        return jsonify({"message": "User not found."}), 404

    return jsonify(serialize_user(user)), 200

def get_user_by_dni(dni: str):
    """Retrieve a single user by DNI.

    Args:
        dni: DNI of the user to fetch.
    Returns:
        JSON response containing user data or a 404 message.
    """
    normalized_dni = dni.strip()

    user = User.query.filter(func.trim(User.dni) == normalized_dni).first()
    if not user or user.date_deleted:
        return jsonify({"message": "User not found."}), 404

    return jsonify(serialize_user(user)), 200


def get_all_users(user_type: str):
    """Retrieve all users of a specific type.

    Args:
        user_type: The user role to filter by (Student, Teacher, Coordinator).

    Returns:
        JSON response with a list of users or an error message.
    """
    try:
        # Convert user_type string to corresponding Enum value.
        user_enum = UserType[user_type.upper()]
    except KeyError:
        return jsonify({"message": f"Invalid user type: {user_type}"}), 400

    users = User.query.filter_by(type=user_enum).all()
    if not users:
        return jsonify({"message": f"No {user_type.lower()}s found."}), 404

    return jsonify([serialize_user(user) for user in users]), 200


def update_user(user_id: int):
    """Update an existing user’s mutable fields.

    Args:
        user_id: Primary key of the user to update.

    Returns:
        JSON response with updated user data or an error message.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body."}), 400

    # Allowed fields for update (email/type excluded intentionally).
    updatable_fields = [
        "name",
        "surname",
        "profile_picture",
        "accumulated_xp",
        "student_level_id",
        "student_class_id",
    ]

    # Apply updates dynamically.
    for field in updatable_fields:
        if field in data:
            setattr(user, field, data[field])

    try:
        db.session.commit()
        return jsonify({
            "message": "User updated successfully.",
            "user": serialize_user(user)
        }), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 400
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500


def delete_user(user_id: int):
    """Permanently delete a user record from the database.

    Args:
        user_id: Primary key of the user to delete.

    Returns:
        JSON response with confirmation or error message.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully."}), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 400
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500
