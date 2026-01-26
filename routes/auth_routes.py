"""
Authentication routing module.

Maps HTTP endpoints to the corresponding authentication controller functions.
The blueprint defines namespace-only routes; the URL prefix must be assigned
when registering the blueprint in the main Flask application.
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required
from controllers.auth_controller import (
    login_controller,
    me_controller,
    refresh_controller,
    logout_controller,
    reset_password_controller,
    verify_email_controller,
    send_reset_code_controller,
    verify_reset_code_controller
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/login")
def login():
    """
    Authenticate a user and issue JWT cookies.
    Returns:
        The result of the login_controller, which authenticates credentials
        and sets a JWT cookie if authentication succeeds.
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
      401:
        description: Invalid credentials
      500:
        description: Server error
    """
    return login_controller()


@auth_bp.get("/api/me")
@jwt_required()
def me():
    """
    Return the authenticated user's profile.
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


@auth_bp.post("/api/refresh")
@jwt_required()
def refresh():
    """
    Refresh the JWT cookie for the authenticated user.
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


@auth_bp.post("/api/logout")
@jwt_required()
def logout():
    """
    Clear the JWT cookie and log the user out.
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


@auth_bp.get("/api/verify/<token>")
def verify(token):
    """
    Verify a user's email using a signed token.
    ---
    tags:
      - Auth
    summary: Verifies the user's email
    description: Validate the signed verification token and activate the account.
    responses:
      200:
        description: Email verified
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Invalid or expired token
      500:
        description: Server error
    """
    return verify_email_controller(token)


@auth_bp.post("/api/forgot-password/send")
def forgot_password_send():
    """
    Send a password reset code to a user's email.
    ---
    tags:
      - Auth
    summary: Send password reset code
    description: Send a password reset code to the user's email.
    responses:
      200:
        description: Code sent
      400:
        description: Invalid email or request
      500:
        description: Server error
    """
    return send_reset_code_controller()


@auth_bp.post("/api/forgot-password/verify")
def forgot_password_verify():
    """
    Verify a password reset code.
    ---
    tags:
      - Auth
    summary: Verify password reset code
    description: Verify the password reset code provided by the user.
    responses:
      200:
        description: Code verified
      400:
        description: Invalid or expired code
      500:
        description: Server error
    """
    return verify_reset_code_controller()


@auth_bp.post("/api/reset-password")
def forgot_password_reset():
    """
    Reset the user's password after verification.
    ---
    tags:
      - Auth
    summary: Reset user password
    description: Reset the user's password to the one he submitted.
    responses:
      200:
        description: Password reset successful
      400:
        description: Invalid request or weak password
      403:
        description: Verification required
      500:
        description: Server error
    """
    return reset_password_controller()
