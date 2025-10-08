"""Blueprint routes for user management.

Defines endpoints for creating, retrieving, updating, and deleting users
by type (Student, Teacher, Coordinator). Delegates logic to controller functions.
"""

from flask import Blueprint
from controllers.user_controller import (
    create_user as controller_create_user,
    get_user as controller_get_user,
    update_user as controller_update_user,
    delete_user as controller_delete_user,
    get_all_users as controller_get_all_users,
)

# Create a Blueprint dedicated to user-related routes.
user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/api/user/student", methods=["POST"])
def create_student():
    """HTTP POST endpoint to create a Student user."""
    return controller_create_user(user_type="Student")


@user_bp.route("/api/user/teacher", methods=["POST"])
def create_teacher():
    """HTTP POST endpoint to create a Teacher user."""
    return controller_create_user(user_type="Teacher")


@user_bp.route("/api/user/coordinator", methods=["POST"])
def create_coordinator():
    """HTTP POST endpoint to create a Coordinator user."""
    return controller_create_user(user_type="Coordinator")


@user_bp.route("/api/user/<int:user_id>", methods=["GET"])
def get_user_route(user_id: int):
    """HTTP GET endpoint to retrieve a user by ID.

    Args:
        user_id: Primary key of the user to retrieve.
    """
    return controller_get_user(user_id)


# ---------------------------------------------------------------------------
# Bulk retrieval endpoints by role
# ---------------------------------------------------------------------------

@user_bp.route("/api/user/student", methods=["GET"])
def get_all_students():
    """HTTP GET endpoint to retrieve all Student users."""
    return controller_get_all_users("Student")


@user_bp.route("/api/user/teacher", methods=["GET"])
def get_all_teachers():
    """HTTP GET endpoint to retrieve all Teacher users."""
    return controller_get_all_users("Teacher")


@user_bp.route("/api/user/coordinator", methods=["GET"])
def get_all_coordinators():
    """HTTP GET endpoint to retrieve all Coordinator users."""
    return controller_get_all_users("Coordinator")


# ---------------------------------------------------------------------------
# Update and delete routes
# ---------------------------------------------------------------------------

@user_bp.route("/api/user/<int:user_id>", methods=["PUT"])
def update_user_route(user_id: int):
    """HTTP PUT endpoint to update a user by ID.

    Args:
        user_id: Primary key of the user to update.
    """
    return controller_update_user(user_id)


@user_bp.route("/api/user/<int:user_id>", methods=["DELETE"])
def delete_user_route(user_id: int):
    """HTTP DELETE endpoint to remove (soft-delete) a user by ID.

    Args:
        user_id: Primary key of the user to delete.
    """
    return controller_delete_user(user_id)
