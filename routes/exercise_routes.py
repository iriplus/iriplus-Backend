"""Blueprint routes for the Exercise entity.

This module defines the HTTP endpoints for CRUD operations on Exercise.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint
from controllers.exercise_controller import (
    create_exercise as controller_create_exercise,
    get_all_exercises as controller_get_all_exercises,
    get_exercise_by_id as controller_get_exercise_by_id,
    update_exercise as controller_update_exercise,
    delete_exercise as controller_delete_exercise,
)

# Create a Blueprint for Exercise-related routes.
exercise_bp = Blueprint("exercise_bp", __name__)


@exercise_bp.route("/api/exercise", methods=["POST"])
def create_exercise():
    """HTTP POST endpoint to create a new exercise."""
    return controller_create_exercise(exercise_archetype="Test archetype")


@exercise_bp.route("/api/exercise", methods=["GET"])
def get_all_exercises():
    """HTTP GET endpoint to retrieve all Exercises."""
    return controller_get_all_exercises()


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["GET"])
def get_exercise_by_id(exercise_id: int):
    """HTTP GET endpoint to retrieve a Exercise by its ID.

    Args:
        exercise_id: Primary key of the Exercise to retrieve.
    """
    return controller_get_exercise_by_id(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["PUT"])
def update_exercise(exercise_id: int):
    """HTTP PUT endpoint to update an existing Exercise.

    Args:
        exercise_id: Primary key of the Exercise to update.
    """
    return controller_update_exercise(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id: int):
    """HTTP DELETE endpoint to soft-delete a Exercise.

    Args:
        exam_id: Primary key of the Exercise to delete.
    """
    return controller_delete_exercise(exercise_id)
