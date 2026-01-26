"""Blueprint routes for the Level entity.

This module defines the HTTP endpoints related to Level operations.
It delegates the actual business logic to the level_controller.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from orm_models import db, User
from controllers.level_controller import create_level as controller_create_level
from controllers.level_controller import get_all_levels as get_all_levels_controller
from controllers.level_controller import get_level_by_id as get_one_controller
from controllers.level_controller import update_level as update_level_controller
from controllers.level_controller import soft_delete_level as delete_level_controller
from utils.types_enum import UserType
from utils.decorators import roles_required

level_bp = Blueprint("level_bp", __name__)


@level_bp.route("/api/level", methods=["POST"])
@roles_required(UserType.COORDINATOR)
def create_level():
    """
    Create a new Level (Coordinator only).
    ---
    tags:
      - Level
    summary: Create a new Level
    description: Create a new Level entity with description, cosmetic and min_xp.
    responses:
      201:
        description: Level created successfully
      403:
        description: Forbidden
      500:
        description: Server error
    """
    return controller_create_level()


@level_bp.route("/api/level", methods=["GET"])
@roles_required(UserType.COORDINATOR, UserType.TEACHER)
def get_all_levels():
    """
    List all Levels (Coordinator and Teacher)
    ---
    tags:
      - Level
    summary: List all non-deleted Levels
    description: Retrieve a list of all Levels that have not been soft-deleted.
    responses:
      200:
        description: OK
      403:
        description: Forbidden
      500:
        description: Server error
    """
    return get_all_levels_controller()


@level_bp.route("/api/level/<int:level_id>", methods=["GET"])
def get_one_level(level_id: int):
    """
    Retrieve a Level by ID respecting role restrictions.
    ---
    tags:
      - Level
    summary: Retrieve a Level
    description: Return a Level by its ID if it exists and is not soft-deleted.
    responses:
      200:
        description: Level found
      403:
        description: Forbidden
      404:
        description: Level not found
      500:
        description: Server error
    """

    verify_jwt_in_request()
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user or user.date_deleted:
        return jsonify({"message": "User not found"}), 404

    # Coordinator and Teacher can read any level
    if user.type in (UserType.COORDINATOR, UserType.TEACHER):
        return get_one_controller(level_id)

    # Student can only read their own level
    if user.type == UserType.STUDENT:
        if user.student_level_id == level_id:
            return get_one_controller(level_id)
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"message": "Forbidden"}), 403


@level_bp.route("/api/level/<int:level_id>", methods=["PUT"])
@roles_required(UserType.COORDINATOR)
def update_level(level_id: int):
    """
    Update a Level (Coordinator only).
    ---
    tags:
      - Level
    summary: Update an existing Level
    description: Update fields of a Level entity.
    responses:
      200:
        description: Level updated
      403:
        description: Forbidden
      404:
        description: Level not found
      500:
        description: Server error
    """
    return update_level_controller(level_id)


@level_bp.route("/api/level/<int:level_id>", methods=["DELETE"])
@roles_required(UserType.COORDINATOR)
def delete_level(level_id: int):
    """
    Soft delete a Level (Coordinator only).
    ---
    tags:
      - Level
    summary: Soft delete a Level
    description: Perform a soft delete of a Level by setting date_deleted.
    responses:
      200:
        description: Level deleted
      403:
        description: Forbidden
      404:
        description: Level not found
      500:
        description: Server error
    """
    return delete_level_controller(level_id)
