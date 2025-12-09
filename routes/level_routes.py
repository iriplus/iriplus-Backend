"""Blueprint routes for the Level entity.

This module defines the HTTP endpoints related to Level operations.
It delegates the actual business logic to the level_controller.
"""

from flask import Blueprint
from controllers.level_controller import create_level as controller_create_level
from controllers.level_controller import get_all_levels as get_all_levels_controller
from controllers.level_controller import get_level_by_id as get_one_controller
from controllers.level_controller import update_level as update_level_controller
from controllers.level_controller import soft_delete_level as delete_level_controller

# Create a Blueprint for Level-related routes.
level_bp = Blueprint("level_bp", __name__)


@level_bp.route("/api/level", methods=["POST"])
def create_level():
    """
    Create a new Level
    ---
    tags:
      - Level
    summary: Create a new Level
    description: Create a new Level entity with description, cosmetic and min_xp.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LevelInput'
    responses:
      201:
        description: Level created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                id:
                  type: integer
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_level()


@level_bp.route("/api/level", methods=["GET"])
def get_all_levels():
    """
    List all Levels
    ---
    tags:
      - Level
    summary: List all non-deleted Levels
    description: Retrieve a list of all Levels that have not been soft-deleted.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Level'
      500:
        description: Server error
    """
    return get_all_levels_controller()


@level_bp.route("/api/level/<int:level_id>", methods=["GET"])
def get_one_level(level_id: int):
    """
    Get a Level by ID
    ---
    tags:
      - Level
    summary: Retrieve a Level
    description: Return a Level by its ID if it exists and is not soft-deleted.
    parameters:
      - in: path
        name: level_id
        schema:
          type: integer
        required: true
        description: Primary key of the Level
    responses:
      200:
        description: Level found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Level'
      404:
        description: Level not found
      500:
        description: Server error
    """
    return get_one_controller(level_id)


@level_bp.route("/api/level/<int:level_id>", methods=["PUT"])
def update_level(level_id: int):
    """
    Update a Level
    ---
    tags:
      - Level
    summary: Update an existing Level
    description: Update fields of a Level entity.
    parameters:
      - in: path
        name: level_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LevelInput'
    responses:
      200:
        description: Level updated
      400:
        description: Invalid JSON body or invalid fields
      404:
        description: Level not found
      500:
        description: Server error
    """
    return update_level_controller(level_id)


@level_bp.route("/api/level/<int:level_id>", methods=["DELETE"])
def delete_level(level_id: int):
    """
    Soft delete a Level
    ---
    tags:
      - Level
    summary: Soft delete a Level
    description: Perform a soft delete of a Level by setting date_deleted.
    parameters:
      - in: path
        name: level_id
        schema:
          type: integer
        required: true
    responses:
      200:
        description: Level deleted
      404:
        description: Level not found
      500:
        description: Server error
    """
    return delete_level_controller(level_id)
