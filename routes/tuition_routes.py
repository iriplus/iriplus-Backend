from flask import Blueprint
from flask_jwt_extended import jwt_required

from controllers.tuition_controller import upload_tuitions_controller
from utils.types_enum import UserType
from utils.decorators import roles_required

tuition_bp = Blueprint("tuition_bp", __name__)


@tuition_bp.route("/api/tuitions/upload", methods=["POST"])
@jwt_required()
@roles_required(UserType.COORDINATOR)
def upload_tuitions():
    """
    Upload an Excel/CSV file to update student tuition data.
    ---
    tags:
      - Tuitions
    summary: Upload tuition file
    description: |
      Receives a CSV/XLS/XLSX file with the required columns:
      dni, last_paid_month, payment_date.
      Validates the full file before updating the database.
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
    responses:
      200:
        description: Tuitions updated successfully
      400:
        description: Validation error
      403:
        description: Forbidden
      500:
        description: Server error
    """
    return upload_tuitions_controller()