import datetime
from flask import request, jsonify
from orm_models import db, Level

def create_level():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message: Invalid JSON body"}), 400
    try:
        description = data["description"]
        cosmetic = data["cosmetic"]
        min_xp = data["min_xp"]

        level = Level(description = description, cosmetic = cosmetic, min_xp = min_xp, date_created = datetime.datetime.now())

        db.session.add(level)
        db.session.commit()

        return jsonify({"message": "Level created succesfully", "id": level.id}), 201
    except Exception as e:
        return jsonify({"message": f"Something went wrong: {e}"}),501
