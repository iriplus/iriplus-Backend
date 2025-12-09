"""Blueprint routes for user management.

Defines endpoints for creating, retrieving, updating, and deleting users
by type (Student, Teacher, Coordinator). Delegates logic to controller functions.
"""

from flask import Blueprint
from controllers.user_controller import (
    create_user as controller_create_user,
    get_user as controller_get_user,
    update_user as controller_update_user,
    delete_user as controller_delete_user,
    get_all_users as controller_get_all_users,
)
from utils.types_enum import UserType

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/api/user/student", methods=["POST"])
def create_student():
    """
    Create a Student user
    ---
    tags:
      - User
    summary: Create a Student user
    description: Create a new User entity with role Student.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserInput'
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_user(user_type=UserType.STUDENT)


@user_bp.route("/api/user/teacher", methods=["POST"])
def create_teacher():
    """
    Create a Teacher user
    ---
    tags:
      - User
    summary: Create a Teacher user
    description: Create a new User entity with role Teacher.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserInput'
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_user(user_type=UserType.TEACHER)


@user_bp.route("/api/user/coordinator", methods=["POST"])
def create_coordinator():
    """
    Create a Coordinator user
    ---
    tags:
      - User
    summary: Create a Coordinator user
    description: Create a new User entity with role Coordinator.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserInput'
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_user(user_type=UserType.COORDINATOR)


@user_bp.route("/api/user/<int:user_id>", methods=["GET"])
def get_user_route(user_id: int):
    """
    Get a User by ID
    ---
    tags:
      - User
    summary: Retrieve a User
    description: Get a User by its ID.
    parameters:
      - in: path
        name: user_id
        schema:
          type: integer
        required: true
        description: Primary key of the User
    responses:
      200:
        description: User found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      404:
        description: User not found
      500:
        description: Server error
    """
    return controller_get_user(user_id)


@user_bp.route("/api/user/student", methods=["GET"])
def get_all_students():
    """
    List all Student users
    ---
    tags:
      - User
    summary: List all Students
    description: Retrieve all Users with role Student.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/User'
      500:
        description: Server error
    """
    return controller_get_all_users("Student")


@user_bp.route("/api/user/teacher", methods=["GET"])
def get_all_teachers():
    """
    List all Teacher users
    ---
    tags:
      - User
    summary: List all Teachers
    description: Retrieve all Users with role Teacher.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/User'
      500:
        description: Server error
    """
    return controller_get_all_users("Teacher")


@user_bp.route("/api/user/coordinator", methods=["GET"])
def get_all_coordinators():
    """
    List all Coordinator users
    ---
    tags:
      - User
    summary: List all Coordinators
    description: Retrieve all Users with role Coordinator.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/User'
      500:
        description: Server error
    """
    return controller_get_all_users("Coordinator")


@user_bp.route("/api/user/<int:user_id>", methods=["PUT"])
def update_user_route(user_id: int):
    """
    Update a User
    ---
    tags:
      - User
    summary: Update a User
    description: Update fields of an existing User.
    parameters:
      - in: path
        name: user_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserInput'
    responses:
      200:
        description: User updated
      400:
        description: Invalid JSON body or invalid fields
      404:
        description: User not found
      500:
        description: Server error
    """
    return controller_update_user(user_id)


@user_bp.route("/api/user/<int:user_id>", methods=["DELETE"])
def delete_user_route(user_id: int):
    """
    Soft delete a User
    ---
    tags:
      - User
    summary: Soft delete a User
    description: Soft-delete a User by setting date_deleted.
    parameters:
      - in: path
        name: user_id
        schema:
          type: integer
        required: true
    responses:
      200:
        description: User deleted
      404:
        description: User not found
      500:
        description: Server error
    """
    return controller_delete_user(user_id)
