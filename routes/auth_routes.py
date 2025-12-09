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
    """
    return logout_controller()
