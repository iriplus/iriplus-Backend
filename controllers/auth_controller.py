"""
Authentication controller module.

Handles login, token-protected user info, refresh, and logout
using JWT stored in HttpOnly cookies.
"""

from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
import bcrypt
from orm_models import User, db


def login_controller():
    """
    Authenticate a user with email and password.

    Expected JSON body:
        {
            "email": "<string>",
            "password": "<string>"
        }

    On success:
        - Generates JWT access token
        - Stores token in HttpOnly cookie
        - Returns JSON {"msg": "login ok"}

    Returns:
        200 OK on successful authentication
        400 Bad Request if email or password missing
        401 Unauthorized if user does not exist or password mismatch
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    # Basic validation of request body
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"msg": "email and password required"}), 400

    # Fetch user record
    user = User.query.filter_by(email=email).first()

    # Reject if user does not exist or stored password is not valid
    if not user or not isinstance(user.passwd, str):
        return jsonify({"msg": "Invalid credentials"}), 401

    # Compare plaintext password with stored bcrypt hash
    if not bcrypt.checkpw(password.encode("utf-8"), user.passwd.encode("utf-8")):
        return jsonify({"msg": "Invalid credentials"}), 401

    # Generate JWT and store in HttpOnly cookie
    token = create_access_token(identity=str(user.id))
    response = jsonify({"msg": "login ok"})
    set_access_cookies(response, token)

    return response, 200


@jwt_required()
def me_controller():
    """
    Return authenticated user's profile.

    Requires cookie-based JWT.

    Returns:
        200 OK with user info
        404 Not Found if the user ID in token does not match any DB record
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
        },
        200,
    )


@jwt_required()
def refresh_controller():
    """
    Refresh cookie-based JWT for authenticated users.

    Returns:
        200 OK with new token stored in cookie
    """
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=str(user_id))
    response = jsonify({"msg": "token refreshed"})
    set_access_cookies(response, new_token)

    return response, 200


def logout_controller():
    """
    Log out user by clearing the JWT cookie.

    Returns:
        200 OK
    """
    response = jsonify({"msg": "logout ok"})
    unset_jwt_cookies(response)

    return response, 200
