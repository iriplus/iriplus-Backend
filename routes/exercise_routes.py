"""Blueprint routes for the Exercise entity.

This module defines the HTTP endpoints related to Exercise type operations.
It delegates the actual business logic to the exercise_controller.
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required

from controllers.exercise_controller import create_exercise
from controllers.exercise_controller import get_all_exercises
from controllers.exercise_controller import get_exercise_by_id
from controllers.exercise_controller import soft_delete_exercise
from controllers.exercise_controller import update_exercise
from utils.decorators import roles_required
from utils.types_enum import UserType

exercise_bp = Blueprint("exercise_bp", __name__)


@exercise_bp.route("/api/exercise", methods=["POST"])
@roles_required(UserType.COORDINATOR)
def create_exercise_route():
    """Create a new Exercise type.

    Coordinator only.

    Returns:
        201 if the Exercise type was created successfully.
        400 if the request body is invalid.
        403 if the user is forbidden.
        409 if the name already exists.
        500 if a server error occurs.
    """
    return create_exercise()


@exercise_bp.route("/api/exercise", methods=["GET"])
@jwt_required()
def get_all_exercises_route():
    """Return all active Exercise types.

    Coordinator only.

    Returns:
        200 with the list of active Exercise types.
        403 if the user is forbidden.
        500 if a server error occurs.
    """
    return get_all_exercises()


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["GET"])
@jwt_required()
def get_exercise_by_id_route(exercise_id: int):
    """Return one active Exercise type by id.

    Args:
        exercise_id: Primary key of the Exercise type.

    Returns:
        200 if the Exercise type exists.
        403 if the user is forbidden.
        404 if the Exercise type was not found.
        500 if a server error occurs.
    """
    return get_exercise_by_id(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["PUT"])
@roles_required(UserType.COORDINATOR)
def update_exercise_route(exercise_id: int):
    """Update an existing Exercise type.

    Coordinator only.

    Args:
        exercise_id: Primary key of the Exercise type.

    Returns:
        200 if the Exercise type was updated successfully.
        400 if the request body is invalid.
        403 if the user is forbidden.
        404 if the Exercise type was not found.
        409 if the requested name already exists.
        500 if a server error occurs.
    """
    return update_exercise(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["DELETE"])
@roles_required(UserType.COORDINATOR)
def delete_exercise_route(exercise_id: int):
    """Soft-delete an existing Exercise type.

    Coordinator only.

    Args:
        exercise_id: Primary key of the Exercise type.

    Returns:
        200 if the Exercise type was deleted successfully.
        403 if the user is forbidden.
        404 if the Exercise type was not found.
        500 if a server error occurs.
    """
    return soft_delete_exercise(exercise_id)
