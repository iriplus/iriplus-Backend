"""
Authentication routes.

Maps HTTP endpoints to the corresponding controller functions.
Blueprint is namespace-only; URL prefix must be assigned in app.py.
"""

from flask import Blueprint
from controllers.auth_controller import (
    login_controller,
    me_controller,
    refresh_controller,
    logout_controller,
)

# Blueprint name must be unique across the application
auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """
    Login endpoint.
    Delegates authentication to login_controller.
    """
    return login_controller()


@auth_bp.get("/me")
def me():
    """
    Get authenticated user profile.
    """
    return me_controller()


@auth_bp.post("/refresh")
def refresh():
    """
    Refresh JWT cookie for authenticated user.
    """
    return refresh_controller()


@auth_bp.post("/logout")
def logout():
    """
    Logout endpoint. Clears JWT cookie.
    """
    return logout_controller()
