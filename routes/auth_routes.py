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
    User login
    ---
    tags:
      - Auth
    summary: Authenticate a user and set JWT cookies
    description: Validate user credentials and issue JWT cookies for authentication.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LoginInput'
    responses:
      200:
        description: Login successful
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AuthResponse'
      400:
        description: Invalid credentials
      500:
        description: Server error
    Handle user login requests.

    Returns:
        The result of the login_controller, which authenticates credentials
        and sets a JWT cookie if authentication succeeds.
    """
    return login_controller()


@auth_bp.get("/me")
def me():
    """
    Get current authenticated user
    ---
    tags:
      - Auth
    summary: Get the authenticated user profile
    description: Return the profile of the authenticated user based on the JWT cookie.
    responses:
      200:
        description: Authenticated user info
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      401:
        description: Not authenticated
      500:
        description: Server error
    Return the authenticated user profile.

    Returns:
        The JSON response produced by me_controller, including user details
        of the authenticated session.
    """
    return me_controller()


@auth_bp.post("/refresh")
def refresh():
    """
    Refresh JWT session
    ---
    tags:
      - Auth
    summary: Refresh JWT cookie
    description: Refresh the authentication token using the existing JWT cookie.
    responses:
      200:
        description: JWT refreshed
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      401:
        description: Not authenticated
      500:
        description: Server error
    Refresh the user's JWT session cookie.

    Returns:
        The JSON response from refresh_controller with a renewed JWT cookie.
    """
    return refresh_controller()


@auth_bp.post("/logout")
def logout():
    """
    Logout user
    ---
    tags:
      - Auth
    summary: Logout user and clear authentication cookie
    description: Clear the JWT cookie and invalidate authentication.
    responses:
      200:
        description: Logged out
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      401:
        description: Not authenticated
      500:
        description: Server error
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
