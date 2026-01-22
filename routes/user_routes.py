"""Blueprint routes for user management.

Defines endpoints for creating, retrieving, updating, and deleting users
by type (Student, Teacher, Coordinator). Delegates logic to controller functions.
"""

from flask import Blueprint
from controllers.user_controller import (
    create_user as controller_create_user,
    register_student as controller_register_student,
    get_user as controller_get_user,
    update_user as controller_update_user,
    delete_user as controller_delete_user,
    get_all_users as controller_get_all_users,
    get_user_by_email as controller_get_user_by_email,
    get_user_by_dni as controller_get_user_by_dni,
)
from utils.types_enum import UserType

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/api/user/student", methods=["POST"])
def register_student():
    """
    Create a Student user
    ---
    tags:
      - User
    summary: Register a new Student account
    description: Public endpoint to create a Student account and send a verification email
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/StudentInput'
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid data
      404:
        description: Class not found
      409:
        description: Email or DNI already exists
      422:
        description: Class full
      500:
        description: Server error
    """
    return controller_register_student()


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

@user_bp.route("/api/user/email/<string:email>", methods=["GET"])
def get_user_by_email(email: str):
    """
    Get a User by email
    ---
    tags:
      - User
    summary: Retrieve a User by email
    description: Get a User by its email address.
    parameters:
      - in: path
        name: email
        schema:
          type: string
        required: true
        description: Email address of the User
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
    return controller_get_user_by_email(email)

@user_bp.route("/api/user/dni/<string:dni>", methods=["GET"])
def get_user_by_dni(dni: str):
    """
    Get a User by DNI
    ---
    tags:
      - User
    summary: Retrieve a User by DNI
    description: Get a User by its DNI.
    parameters:
      - in: path
        name: dni
        schema:
          type: string
        required: true
        description: DNI of the User
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
    return controller_get_user_by_dni(dni)

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
