"""Blueprint routes for authentication endpoints.

This module defines routes related to user authentication.
It delegates the login logic to the corresponding controller function.
"""

from flask import Blueprint
from controllers.auth_controller import login as controller_login

# Create a Blueprint dedicated to authentication operations.
auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """HTTP POST endpoint to authenticate a user.

    Expects a JSON payload with email and password.
    Delegates validation to the controller.
    """
    return controller_login()
