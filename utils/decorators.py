from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from orm_models import db, User
from utils.types_enum import UserType


def roles_required(*allowed_roles: UserType):
    """
    Protect a route requiring authentication and specific user roles.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 1) Validate JWT (cookie)
            verify_jwt_in_request()

            # 2) Get current user
            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id))

            if not user or user.date_deleted:
                return jsonify({"message": "User not found"}), 404

            # 3) Role validation
            if user.type not in allowed_roles:
                return jsonify({"message": "Forbidden"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def self_or_coordinator(param_name="user_id"):
    """
    Determine if the user is trying to access a route for himself or for another coordinator
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Validate JWT (Cookie)
            verify_jwt_in_request()

            # Get current user
            current_user_id = int(get_jwt_identity())
            current_user = db.session.get(User, current_user_id)

            if not current_user or current_user.date_deleted:
                return jsonify({"message": "User not found"}), 404

            # Get target user
            target_user_id = kwargs.get(param_name)
            target_user = db.session.get(User, target_user_id)

            if not target_user or target_user.date_deleted:
                return jsonify({"message": "Target user not found"}), 404

            #Self access?
            if current_user.id == target_user.id:
                return fn(*args, **kwargs)

            # If not self access, is it other coordinator?
            if (
                current_user.type == UserType.COORDINATOR
                and target_user.type != UserType.COORDINATOR
            ):
                return fn(*args, **kwargs)

            return jsonify({"message": "Forbidden"}), 403

        return wrapper
    return decorator

def self_only(param_name="user_id"):
    """
    Determine if the user is trying to access to a self-route
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Validate JWT (Cookie)
            verify_jwt_in_request()

            # Get current user and target user
            current_user_id = int(get_jwt_identity())
            target_user_id = kwargs.get(param_name)

            if current_user_id != target_user_id:
                return jsonify({"message": "Forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapper
    return decorator
