import datetime
from flask import request, jsonify
from orm_models import db, Class

def create_class():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400
    try:
        class_code = data["class_code"]
        description = data["description"]
        suggested_level = data["suggested_level"]
        max_capacity = data["max_capacity"]

        new_class = Class(
            class_code=class_code,
            description=description,
            suggested_level=suggested_level,
            max_capacity=max_capacity,
            date_created=datetime.datetime.now()
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({"message": "Class created successfully", "id": new_class.id}), 201
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}), 500
    

def get_all_classes():
    try:
        classes = Class.query.filter_by(date_deleted=None).all()
        result = []
        for c in classes:
            result.append({
                "id": c.id,
                "class_code": c.class_code,
                "description": c.description,
                "suggested_level": c.suggested_level,
                "max_capacity": c.max_capacity,
                "date_created": c.date_created
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}), 500


def get_class_by_id(class_id):
    try:
        c = Class.query.get(class_id)
        if not c or c.date_deleted:
            return jsonify({"message": "Class not found"}), 404

        return jsonify({
            "id": c.id,
            "class_code": c.class_code,
            "description": c.description,
            "suggested_level": c.suggested_level,
            "max_capacity": c.max_capacity,
            "date_created": c.date_created
        }), 200
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}), 500


def update_class(class_id):
    c = Class.query.get(class_id)
    if not c or c.date_deleted:
        return jsonify({"message": "Class not found"}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400
    try:
        class_code = data.get("class_code", c.class_code)
        description = data.get("description", c.description)
        suggested_level = data.get("suggested_level", c.suggested_level)
        max_capacity = data.get("max_capacity", c.max_capacity)

        c.class_code = class_code
        c.description = description
        c.suggested_level = suggested_level
        c.max_capacity = max_capacity

        db.session.commit()
        return jsonify({"message": "Class updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}), 500


def delete_class(class_id):
    c = Class.query.get(class_id)
    if not c or c.date_deleted:
        return jsonify({"message": "Class not found"}), 404
    try:
        c.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message": "Class deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}), 500
    