"""
Authentication controller.

Provides authentication features using JWT stored in HttpOnly cookies:
- Login
- Return authenticated user profile (/me)
- Refresh JWT cookie
- Logout
- Verify user email address using signed verification tokens

Email verification tokens are generated and validated via itsdangerous.
"""

import os
import random
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from flask_mail import Message
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from orm_models import User, db
from extensions.mail_extension import mail


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def normalize_email(email: str) -> str:
    """
    Normalize an email address by stripping whitespace and converting to lowercase.
    Args:
        email: The email address to normalize.
    Returns:
        The normalized email address.
    """
    return email.strip().lower()

def generate_code() -> str:
    """
    Generate a random 6-digit code.
    Returns:
        A string representing a zero-padded 6-digit code.
    """
    return f"{random.randint(0, 999999):06d}"

def get_reset_ttl_seconds() -> int:
    """
    Get the password reset TTL in seconds from the environment variable.
    Returns:
        The TTL in seconds, defaulting to 900 (15 minutes).
    """
    raw = os.getenv("PASSWORD_RESET_TTL_SECONDS", "900")
    try:
        return int(raw)
    except ValueError:
        return 900

def reset_code_key(email: str) -> str:
    """
    Generate the Redis key for storing a password reset code.
    Args:
        email: The user's email address.
    Returns:
        A string representing the Redis key for the reset code.
    """
    return f"pwdreset:code:{normalize_email(email)}"

def confirm_verification_token(token: str, expiration=3600):
    """
    Validate a signed email verification token.

    Args:
        token: Token received from the verification URL.
        expiration: Maximum allowed age of the token in seconds.

    Returns:
        The decoded email address if the token is valid.
        None if the token is invalid or expired.
    """
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="email-verification", max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


# ----------------------------------------------------------
# LOGIN
# ----------------------------------------------------------

def login_controller():
    """
    Authenticate user credentials and issue a JWT cookie.

    Expected JSON body:
        {
            "email": "<string>",
            "password": "<string>"
        }

    On success:
        Stores JWT access token in an HttpOnly cookie
        and returns {"msg": "login ok"}

    Returns:
        200 OK on valid login.
        400 if required fields are missing.
        401 if credentials are invalid.
        403 if the user's email is not yet verified.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"msg": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not isinstance(user.passwd, str):
        return jsonify({"msg": "Invalid credentials"}), 401

    # ----------- NEW: bloquear si no verificó email ----------
    if not user.is_verified:
        return jsonify({"msg": "Email not verified"}), 403

    if not bcrypt.checkpw(password.encode("utf-8"), user.passwd.encode("utf-8")):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    response = jsonify({"msg": "login ok"})
    set_access_cookies(response, token)

    return response, 200


# ----------------------------------------------------------
# GET PROFILE
# ----------------------------------------------------------

@jwt_required()
def me_controller():
    """
    Return the profile of the authenticated user.

    Requires:
        A valid JWT access token in an HttpOnly cookie.

    Returns:
        200 OK with user fields.
        404 if the authenticated user cannot be found.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return (
        {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "type": user.type.value,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified,   # opcional
        },
        200,
    )


# ----------------------------------------------------------
# REFRESH
# ----------------------------------------------------------

@jwt_required()
def refresh_controller():
    """
    Refresh the user's JWT and reissue an HttpOnly cookie.

    Returns:
        200 OK with {"msg": "token refreshed"}.
    """
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=str(user_id))
    response = jsonify({"msg": "token refreshed"})
    set_access_cookies(response, new_token)

    return response, 200


# ----------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------

def logout_controller():
    """
    Clear the JWT cookie and log the user out.

    Returns:
        200 OK with {"msg": "logout ok"}.
    """
    response = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(response)
    return response, 200


# ----------------------------------------------------------
# VERIFICAR EMAIL
# ----------------------------------------------------------

def verify_email_controller(token: str):
    """
    Verify a user's email address based on a signed token.

    Args:
        token: The token included in the verification URL.

    Returns:
        200 OK if the email was successfully verified.
        400 if the token is invalid or expired.
        404 if no user matches the decoded email address.
    """
    email = confirm_verification_token(token)

    if not email:
        return jsonify({"msg": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.is_verified:
        return jsonify({"msg": "Email already verified"}), 200

    user.is_verified = True
    db.session.commit()

    return jsonify({"msg": "Email verified successfully"}), 200

# ----------------------------------------------------------
# SEND CODE FOR PASSWORD RESET
# ----------------------------------------------------------

def send_reset_code_controller():
    """
    Send a password reset code to the user's email.
    Expected JSON body:
        {
            "email": "<string>"
        }
    Returns:
        200 OK if the code was sent.
        400 if the email field is missing.
        404 if no user matches the provided email address.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not isinstance(email, str) or not email.strip():
        return jsonify({"msg": "email required"}), 400

    normalized = normalize_email(email)

    user = User.query.filter_by(email=normalized).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    code = generate_code()
    ttl_seconds = get_reset_ttl_seconds()

    redis_client = current_app.extensions["redis_client"]
    key = reset_code_key(normalized)

    # Set code with TTL (overwrites previous code)
    redis_client.setex(key, ttl_seconds, code)

    msg = Message(
        subject="Your password recovery code",
        recipients=[normalized],
        body=(
            f"Your password recovery code is: {code}\n"
            f"It expires in {ttl_seconds // 60} minutes."
        ),
    )
    mail.send(msg)

    return jsonify({"msg": "code sent"}), 200

def verify_reset_code_controller():
    """
    Verify a password reset code sent to the user's email.
    Expected JSON body:
        {
            "email": "<string>",
            "code": "<string>"
        }
    Returns:
        200 OK if the code is valid.
        400 if required fields are missing or the code is invalid/expired.
        404 if no user matches the provided email address.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    code = data.get("code")

    if not isinstance(email, str) or not isinstance(code, str):
        return jsonify({"msg": "email and code required"}), 400

    normalized = normalize_email(email)
    code = code.strip()

    if len(code) != 6 or not code.isdigit():
        return jsonify({"msg": "Invalid or expired code"}), 400

    redis_client = current_app.extensions["redis_client"]
    key = reset_code_key(normalized)

    stored_code = redis_client.get(key)
    if not stored_code:
        return jsonify({"msg": "Invalid or expired code"}), 400

    if stored_code != code:
        return jsonify({"msg": "Invalid or expired code"}), 400

    # One-time use: delete on success
    redis_client.delete(key)

    return jsonify({"msg": "code valid"}), 200
