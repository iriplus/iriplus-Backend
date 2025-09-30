"""Blueprint routes for the Class entity.

This module defines the HTTP endpoints for CRUD operations on Class.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint
from controllers.class_controller import (
    create_class as controller_create_class,
    get_all_classes as controller_get_all_classes,
    get_class_by_id as controller_get_class_by_id,
    update_class as controller_update_class,
    delete_class as controller_delete_class,
)

# Create a Blueprint for Class-related routes.
class_bp = Blueprint("class_bp", __name__)


@class_bp.route("/api/class", methods=["POST"])
def create_class():
    """HTTP POST endpoint to create a new Class."""
    return controller_create_class()


@class_bp.route("/api/class", methods=["GET"])
def get_all_classes():
    """HTTP GET endpoint to retrieve all Classes."""
    return controller_get_all_classes()


@class_bp.route("/api/class/<int:class_id>", methods=["GET"])
def get_class_by_id(class_id: int):
    """HTTP GET endpoint to retrieve a Class by its ID.

    Args:
        class_id: Primary key of the Class to retrieve.
    """
    return controller_get_class_by_id(class_id)


@class_bp.route("/api/class/<int:class_id>", methods=["PUT"])
def update_class(class_id: int):
    """HTTP PUT endpoint to update an existing Class.

    Args:
        class_id: Primary key of the Class to update.
    """
    return controller_update_class(class_id)


@class_bp.route("/api/class/<int:class_id>", methods=["DELETE"])
def delete_class(class_id: int):
    """HTTP DELETE endpoint to soft-delete a Class.

    Args:
        class_id: Primary key of the Class to delete.
    """
    return controller_delete_class(class_id)
