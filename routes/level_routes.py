"""Blueprint routes for the Level entity.

This module defines the HTTP endpoints related to Level operations.
It delegates the actual business logic to the level_controller.
"""

from flask import Blueprint, request, jsonify
from orm_models import db
from controllers.level_controller import create_level as controller_create_level

# Create a Blueprint for Level-related routes.
level_bp = Blueprint("level_bp", __name__)

@level_bp.route("/api/level", methods=["POST"])
def create_level():
    """HTTP POST endpoint to create a new Level.

    The request payload is processed by the controller, which handles
    validation, persistence, and response formatting.
    """
    return controller_create_level()
