"""Blueprint routes for the Class entity.

This module defines the HTTP endpoints for CRUD operations on Class.
Each route delegates its logic to the corresponding controller function.
"""

from flask import Blueprint
from controllers.class_controller import (
    create_class as controller_create_class,
    get_all_classes as controller_get_all_classes,
    get_class_by_id as controller_get_class_by_id,
    update_class as controller_update_class,
    delete_class as controller_delete_class,
    get_class_by_class_code as controller_get_class_by_class_code,
)

# Create a Blueprint for Class-related routes.
class_bp = Blueprint("class_bp", __name__)


@class_bp.route("/api/class", methods=["POST"])
def create_class():
    """
    Create a new Class
    ---
    tags:
      - Class
    summary: Create a new Class
    description: Create a new Class entity.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ClassInput'
    responses:
      201:
        description: Class created successfully
      400:
        description: Invalid JSON body
      500:
        description: Server error
    """
    return controller_create_class()


@class_bp.route("/api/class", methods=["GET"])
def get_all_classes():
    """
    List all Classes
    ---
    tags:
      - Class
    summary: List all Classes
    description: Retrieve all existing Classes.
    responses:
      200:
        description: OK
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Class'
      500:
        description: Server error
    """
    return controller_get_all_classes()


@class_bp.route("/api/class/id/<int:class_id>", methods=["GET"])
def get_class_by_id(class_id: int):
    """
    Get a Class by ID
    ---
    tags:
      - Class
    summary: Retrieve a Class
    description: Return a Class by its ID.
    parameters:
      - in: path
        name: class_id
        schema:
          type: integer
        required: true
        description: Primary key of the Class
    responses:
      200:
        description: Class found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Class'
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_get_class_by_id(class_id)

@class_bp.route("/api/class/code/<string:class_code>", methods=["GET"])
def get_class_by_class_code(class_code: str):
    """
    Get a Class by class_code
    ---
    tags:
      - Class
    summary: Retrieve a Class
    description: Return a Class by its Code.
    parameters:
      - in: path
        name: class_code
        schema:
          type: string
        required: true
        description: Unique code of the Class
    responses:
      200:
        description: Class found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Class'
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_get_class_by_class_code(class_code)


@class_bp.route("/api/class/<int:class_id>", methods=["PUT"])
def update_class(class_id: int):
    """
    Update a Class
    ---
    tags:
      - Class
    summary: Update a Class
    description: Update fields of an existing Class.
    parameters:
      - in: path
        name: class_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ClassInput'
    responses:
      200:
        description: Class updated
      400:
        description: Invalid JSON body or invalid fields
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_update_class(class_id)


@class_bp.route("/api/class/<int:class_id>", methods=["DELETE"])
def delete_class(class_id: int):
    """
    Soft delete a Class
    ---
    tags:
      - Class
    summary: Soft delete a Class
    description: Perform a soft delete of a Class.
    parameters:
      - in: path
        name: class_id
        schema:
          type: integer
        required: true
    responses:
      200:
        description: Class deleted
      404:
        description: Class not found
      500:
        description: Server error
    """
    return controller_delete_class(class_id)
