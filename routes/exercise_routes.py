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
from utils.types_enum import ExerciseArchetype

# Create a Blueprint for Exercise-related routes.
exercise_bp = Blueprint("exercise_bp", __name__)


@exercise_bp.route("/api/exercise", methods=["POST"])
def create_exercise():
    """
    Create a new Exercise
    ---
    tags:
      - Exercise
    summary: Create a new Exercise
    description: Create a new Exercise linked to an Exam.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExerciseInput'
    responses:
      201:
        description: Exercise created
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Exercise'
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_exercise(exercise_archetype=ExerciseArchetype.TEST_ARCHETYPE)


@exercise_bp.route("/api/exercise", methods=["GET"])
def get_all_exercises():
    """
    List all Exercises
    ---
    tags:
      - Exercise
    summary: List all Exercises
    description: Retrieve all Exercises that have not been soft-deleted.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Exercise'
      500:
        description: Server error
    """
    return controller_get_all_exercises()


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["GET"])
def get_exercise_by_id(exercise_id: int):
    """
    Get an Exercise by ID
    ---
    tags:
      - Exercise
    summary: Retrieve an Exercise
    description: Return an Exercise by its ID.
    parameters:
      - in: path
        name: exercise_id
        schema:
          type: integer
        required: true
        description: Primary key of the Exercise
    responses:
      200:
        description: Exercise found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Exercise'
      404:
        description: Exercise not found
      500:
        description: Server error
    """
    return controller_get_exercise_by_id(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["PUT"])
def update_exercise(exercise_id: int):
    """
    Update an Exercise
    ---
    tags:
      - Exercise
    summary: Update an existing Exercise
    description: Update Exercise fields.
    parameters:
      - in: path
        name: exercise_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExerciseInput'
    responses:
      200:
        description: Exercise updated
      400:
        description: Invalid JSON body
      404:
        description: Exercise not found
      500:
        description: Server error
    """
    return controller_update_exercise(exercise_id)


@exercise_bp.route("/api/exercise/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id: int):
    """
    Soft delete an Exercise
    ---
    tags:
      - Exercise
    summary: Soft delete an Exercise
    description: Perform a soft delete by setting date_deleted.
    parameters:
      - in: path
        name: exercise_id
        schema:
          type: integer
        required: true
        description: Primary key of the Exercise
    responses:
      200:
        description: Exercise deleted
      404:
        description: Exercise not found
      500:
        description: Server error
    """
    return controller_delete_exercise(exercise_id)
