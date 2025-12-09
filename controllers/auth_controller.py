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

from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from orm_models import User, db


# ----------------------------------------------------------
# Helper: confirmar token
# ----------------------------------------------------------

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
# VERIFICAR EMAIL — NUEVO
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
