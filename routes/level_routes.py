from flask import Blueprint, request, jsonify
from orm_models import db
from controllers.level_controller import create_level as controller_create_level

level_bp = Blueprint("level_bp", __name__)
@level_bp.route("/api/level", methods=["POST"])
def create_level(): 
    return controller_create_level()