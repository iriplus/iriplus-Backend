"""
Authentication routing module.

Maps HTTP endpoints to the corresponding authentication controller functions.
The blueprint defines namespace-only routes; the URL prefix must be assigned
when registering the blueprint in the main Flask application.
"""

from flask import Blueprint
from controllers.auth_controller import (
    login_controller,
    me_controller,
    refresh_controller,
    logout_controller,
    verify_email_controller,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """
    Handle user login requests.

    Returns:
        The result of the login_controller, which authenticates credentials
        and sets a JWT cookie if authentication succeeds.
    """
    return login_controller()


@auth_bp.get("/me")
def me():
    """
    Return the authenticated user profile.

    Returns:
        The JSON response produced by me_controller, including user details
        of the authenticated session.
    """
    return me_controller()


@auth_bp.post("/refresh")
def refresh():
    """
    Refresh the user's JWT session cookie.

    Returns:
        The JSON response from refresh_controller with a renewed JWT cookie.
    """
    return refresh_controller()


@auth_bp.post("/logout")
def logout():
    """
    Log the user out by clearing the JWT cookie.

    Returns:
        The JSON response from logout_controller confirming logout.
    """
    return logout_controller()


# ----------------------------
# RUTA DE VERIFICACIÓN NUEVA
# ----------------------------
@auth_bp.get("/verify/<token>")
def verify(token):
    """
    Verify user email using a token from the verification email link.

    Args:
        token: The signed verification token included in the activation URL.

    Returns:
        The JSON response from verify_email_controller indicating whether the
        verification was successful, invalid, or expired.
    """
    return verify_email_controller(token)
