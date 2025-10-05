"""Blueprint routes for the Level entity.

This module defines the HTTP endpoints related to Level operations.
It delegates the actual business logic to the level_controller.
"""

from flask import Blueprint, request, jsonify
from orm_models import db
from controllers.level_controller import create_level as controller_create_level
from controllers.level_controller import get_all_levels as get_all_levels_controller
from controllers.level_controller import get_level_by_id as get_one_controller
from controllers.level_controller import update_level as update_level_controller
from controllers.level_controller import soft_delete_level as delete_level_controller

# Create a Blueprint for Level-related routes.
level_bp = Blueprint("level_bp", __name__)

@level_bp.route("/api/level", methods=["POST"])
def create_level():
    """HTTP POST endpoint to create a new Level.

    The request payload is processed by the controller, which handles
    validation, persistence, and response formatting.
    """
    return controller_create_level()

@level_bp.route("/api/level", methods=["GET"])
def get_all_levels():
    """HTTP GET endpoint to retrieve all non-deleted levels.

    Returns:
        Flask Response: JSON array with serialized Level data.
    """
    return get_all_levels_controller()

@level_bp.route("/api/level/<int:level_id>", methods=["GET"])
def get_one_level(level_id: int):
    """HTTP GET endpoint to retrieve a Level by its ID.

    Args:
        level_id (int): Primary key of the Level.

    Returns:
        Flask Response: JSON object with Level data or a 404 message.
    """
    return get_one_controller(level_id)

@level_bp.route("/api/level/<int:level_id>", methods=["PUT"])
def update_level(level_id: int):
    """HTTP PUT endpoint to update a Level.

    Args:
        level_id (int): Primary key of the Level to update.

    Returns:
        Flask Response: JSON message indicating success or failure.
    """
    return update_level_controller(level_id)

@level_bp.route("/api/level/<int:level_id>", methods=["DELETE"])
def delete_level(level_id: int):
    """HTTP DELETE endpoint to perform a soft delete on a Level.

    Args:
        level_id (int): Primary key of the Level to delete.

    Returns:
        Flask Response: JSON message confirming deletion or error details.
    """
    return delete_level_controller(level_id)
