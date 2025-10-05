"""Authentication controller for user login.

This module handles user authentication by verifying credentials
against stored bcrypt password hashes.
"""

import bcrypt
from flask import request, jsonify
from orm_models import User
from user_type_enum import UserType


def login():
    """Authenticate a user by email and password.

    Expects:
        JSON payload with:
            - email (str): user email address.
            - passwd (str): plaintext password.

    Returns:
        JSON response containing user info on success (HTTP 200),
        or an error message with an appropriate status code.
    """
    # Parse incoming JSON request body.
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body."}), 400

    # Extract credentials from request payload.
    email = data.get("email")
    passwd = data.get("passwd")

    # Validate that both fields were provided.
    if not email or not passwd:
        return jsonify({"message": "Email and password are required."}), 400

    # Query the database for a user with the given email.
    user = User.query.filter_by(email=email).first()
    if not user:
        # Return generic error to prevent email enumeration.
        return jsonify({"message": "Invalid email or password."}), 401

    # Compare plaintext password with stored bcrypt hash.
    # Always encode both sides as UTF-8 bytes before comparison.
    if not bcrypt.checkpw(passwd.encode("utf-8"), user.passwd.encode("utf-8")):
        # Same generic message to avoid leaking which field failed.
        return jsonify({"message": "Invalid email or password."}), 401

    # If verification succeeds, return minimal user info (no sensitive data).
    return jsonify(
        {
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "type": user.type.value,  # Enum converted to string.
            },
        }
    ), 200
