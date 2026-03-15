"""
Analytics routing module.

Maps HTTP endpoints to the corresponding analytics controller functions.
The blueprint defines namespace-only routes; no URL prefix is assigned here,
so each endpoint declares its full public path explicitly.
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required
from controllers.analytics_controller import home_analytics_controller

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/api/home")
@jwt_required()
def get_home_analytics():
    """
    Return the Home dashboard analytics for the authenticated user.

    The controller determines which role-specific payload can be returned
    based on the currently authenticated user. For now, only the
    Coordinator dashboard is implemented.

    Returns:
        The result of home_analytics_controller(), including:
        - 200 with the Coordinator dashboard payload
        - 403 if the user is not verified
        - 404 if the user does not exist or is soft-deleted
        - 501 if the authenticated role is not implemented yet
    ---
    tags:
      - Analytics
    summary: Get Home dashboard analytics
    description: >
      Returns the minimum required analytics payload for the authenticated
      user's Home dashboard. The response is role-aware and currently
      implements only the Coordinator dashboard.
    responses:
      200:
        description: Home analytics loaded successfully
      403:
        description: Email not verified
      404:
        description: User not found
      501:
        description: Dashboard analytics not implemented for this role yet
      500:
        description: Server error
    """
    return home_analytics_controller()
