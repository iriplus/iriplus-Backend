"""Controller logic for Level entity.

This module contains the business logic for creating and managing Level
records. Controllers sit between routes (HTTP layer) and models (ORM layer).
"""

import datetime
from flask import request, jsonify
from orm_models import db, Level


def create_level():
    """Create a new Level from JSON request payload.

    Expects JSON with:
        - description (str): description of the level.
        - cosmetic (str): optional cosmetic metadata.
        - min_xp (int): minimum XP required for this level.

    Returns:
        JSON response with a success message and new Level ID,
        or an error response with appropriate HTTP status code.
    """
    # Parse JSON body; return error if missing/invalid.
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    try:
        # Extract required fields from request payload.
        description = data["description"]
        cosmetic = data["cosmetic"]
        min_xp = data["min_xp"]

        # Create Level instance with current timestamp.
        level = Level(
            description=description,
            cosmetic=cosmetic,
            min_xp=min_xp,
            date_created=datetime.datetime.now(),
        )

        # Persist new record in database.
        db.session.add(level)
        db.session.commit()

        return jsonify(
            {"message": "Level created successfully", "id": level.id}
        ), 201

    except Exception as e:  # pylint: disable=broad-except
        # Catch-all for unexpected errors (log in production).
        return jsonify(
            {"message": f"Something went wrong: {e}"}
        ), 501
