from flask import Blueprint
from controllers.class_controller import create_class as controller_create_class, get_all_classes as controller_get_all_classes , get_class_by_id as controller_get_class_by_id, update_class as controller_update_class ,delete_class as controller_delete_class

class_bp = Blueprint("class_bp", __name__)

@class_bp.route("/class", methods=["POST"])
def create_class():
    return controller_create_class()

@class_bp.route("/class", methods=["GET"])
def get_all_classes():
    return controller_get_all_classes()

@class_bp.route("/class/<int:class_id>", methods=["GET"])
def get_class_by_id(class_id):
    return controller_get_class_by_id(class_id)

@class_bp.route("/class/<int:class_id>", methods=["PATCH"])
def update_class(class_id):
    return controller_update_class(class_id)

@class_bp.route("/class/<int:class_id>", methods=["DELETE"])
def delete_class(class_id):
    return controller_delete_class(class_id)
