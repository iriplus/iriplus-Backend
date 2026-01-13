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
    send_reset_code_controller,
    verify_reset_code_controller
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/login")
def login():
    """
    Handle user login requests.

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
      500:
        description: Server error
    """
    return login_controller()


@auth_bp.get("/api/me")
def me():
    """
    Return the authenticated user profile.
    Returns:
        The JSON response produced by me_controller, including user details
        of the authenticated session.
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
def refresh():
    """
    Refresh the user's JWT session cookie.
    Returns:
        The JSON response from refresh_controller with a renewed JWT cookie.
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
def logout():
    """
    Log the user out by clearing the JWT cookie.
    Returns:
        The JSON response from logout_controller confirming logout.
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


# ----------------------------
# RUTA DE VERIFICACIÓN NUEVA
# ----------------------------
@auth_bp.get("/api/verify/<token>")
def verify(token):
    """
    Verifies the user's email
    Returns:
        The JSON response from verify_email_controller confirming the verification
    ---
    tags:
      - Auth
    summary: Verifies the user's email
    description: Documentar bien
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
    return verify_email_controller(token)

# ----------------------------
# RESET PASSWORD CODES
# ----------------------------

@auth_bp.post("/api/forgot-password/send")
def forgot_password_send():
    """
    Send a password reset code to the user's email.
    Returns:
        The JSON response from send_reset_code_controller confirming the code was sent.
    ---
    tags:
      - Auth
    summary: Send password reset code
    description: Send a password reset code to the user's email.
    responses:
      200:
        description: Code sent
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Invalid email or request
      404:
        description: User not found
      500:
        description: Server error
    """
    return send_reset_code_controller()


@auth_bp.post("/api/forgot-password/verify")
def forgot_password_verify():
    """
    Verify the password reset code provided by the user.
    Returns:
        The JSON response from verify_reset_code_controller confirming the code verification.
    ---
    tags:
      - Auth
    summary: Verify password reset code
    description: Verify the password reset code provided by the user.
    responses:
      200:
        description: Code verified
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Invalid email or code or expired code or invalid request
      500:
        description: Server error
    """
    return verify_reset_code_controller()
