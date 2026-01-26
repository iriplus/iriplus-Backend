"""Blueprint routes for the Class entity.

This module defines the HTTP endpoints for CRUD operations on Class.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from orm_models import db, User
from controllers.class_controller import (
    create_class as controller_create_class,
    get_all_classes as controller_get_all_classes,
    get_class_by_id as controller_get_class_by_id,
    update_class as controller_update_class,
    delete_class as controller_delete_class,
    get_class_by_class_code as controller_get_class_by_class_code,
)
from utils.types_enum import UserType
from utils.decorators import roles_required

class_bp = Blueprint("class_bp", __name__)


@class_bp.route("/api/class", methods=["POST"])
@roles_required(UserType.COORDINATOR)
def create_class():
    """
    Create a new Class (Coordinator only).
    ---
    tags:
      - Class
    summary: Create a new Class
    description: Create a new Class entity.
    responses:
      201:
        description: Class created successfully
      403:
        description: Forbidden
      500:
        description: Server error
    """
    return controller_create_class()


@class_bp.route("/api/class", methods=["GET"])
@roles_required(UserType.COORDINATOR, UserType.TEACHER)
def get_all_classes():
    """
    List all Classes (Coordinator and Teacher).
    ---
    tags:
      - Class
    summary: List all Classes
    description: Retrieve all existing Classes.
    responses:
      200:
        description: OK
      403:
        description: Forbidden
      500:
        description: Server error
    """
    return controller_get_all_classes()


@class_bp.route("/api/class/id/<int:class_id>", methods=["GET"])
def get_class_by_id(class_id: int):
    """
    Retrieve a Class by ID respecting role restrictions.
    ---
    tags:
      - Class
    summary: Retrieve a Class
    description: Return a Class by its ID.
    responses:
      200:
        description: Class found
      403:
        description: Forbidden
      404:
        description: Class not found
      500:
        description: Server error
    """

    verify_jwt_in_request()
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user or user.date_deleted:
        return jsonify({"message": "User not found"}), 404

    # Coordinator & Teacher can read any class
    if user.type in (UserType.COORDINATOR, UserType.TEACHER):
        return controller_get_class_by_id(class_id)

    # Student can only read their own class
    if user.type == UserType.STUDENT:
        if user.student_class_id == class_id:
            return controller_get_class_by_id(class_id)
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"message": "Forbidden"}), 403


@class_bp.route("/api/class/code/<string:class_code>", methods=["GET"])
def get_class_by_class_code(class_code: str):
    """
    Retrieve a Class by code respecting role restrictions.
    ---
    tags:
      - Class
    summary: Retrieve a Class
    description: Return a Class by its Code.
    responses:
      200:
        description: Class found
      403:
        description: Forbidden
      404:
        description: Class not found
      500:
        description: Server error
    """

    verify_jwt_in_request()
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user or user.date_deleted:
        return jsonify({"message": "User not found"}), 404

    # Coordinator & Teacher
    if user.type in (UserType.COORDINATOR, UserType.TEACHER):
        return controller_get_class_by_class_code(class_code)

    # Student only their own class
    if user.type == UserType.STUDENT:
        student_class = user.student_class
        if student_class and student_class.class_code == class_code:
            return controller_get_class_by_class_code(class_code)
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"message": "Forbidden"}), 403


@class_bp.route("/api/class/<int:class_id>", methods=["PUT"])
@roles_required(UserType.COORDINATOR)
def update_class(class_id: int):
    """
    Update a Class (Coordinator only).
    ---
    tags:
      - Class
    summary: Update a Class
    description: Update fields of an existing Class.
    responses:
      200:
        description: Class updated
      403:
        description: Forbidden
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_update_class(class_id)


@class_bp.route("/api/class/<int:class_id>", methods=["DELETE"])
@roles_required(UserType.COORDINATOR)
def delete_class(class_id: int):
    """
    Soft delete a Class (Coordinator only)
    ---
    tags:
      - Class
    summary: Soft delete a Class
    description: Perform a soft delete of a Class.
    responses:
      200:
        description: Class deleted
      403:
        description: Forbidden
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_delete_class(class_id)
