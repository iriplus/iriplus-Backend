"""Unit tests for Level CRUD controller endpoints.

This module tests the CRUD functionality of the Level entity
through Flask's built-in test client, using an in-memory SQLite database.

Each test validates the correct HTTP status code, response format,
and database side effects for:
- Create (POST)
- Read all (GET)
- Read by ID (GET)
- Update (PUT)
- Soft delete (DELETE)
- Hard delete (DELETE /hard)
"""

import unittest
import datetime
from typing import cast
from flask import Flask
from orm_models import db, Level
from controllers import level_controller as lc


class TestLevelCRUD(unittest.TestCase):
    """Test suite for CRUD operations of the Level controller."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask app and in-memory database once for all tests."""
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        cls.app = app
        cls.client = app.test_client()

        with app.app_context():
            db.create_all()

            # Register routes manually (avoids dependency on blueprints)
            app.add_url_rule("/api/level", view_func=lc.create_level, methods=["POST"])
            app.add_url_rule("/api/level", view_func=lc.get_all_levels, methods=["GET"])
            app.add_url_rule(
                "/api/level/<int:level_id>",
                view_func=lc.get_level_by_id,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/level/<int:level_id>",
                view_func=lc.update_level,
                methods=["PUT"],
            )
            app.add_url_rule(
                "/api/level/<int:level_id>",
                view_func=lc.soft_delete_level,
                methods=["DELETE"],
            )
            app.add_url_rule(
                "/api/level/<int:level_id>/hard",
                view_func=lc.hard_delete_level,
                methods=["DELETE"],
            )

    def setUp(self):
        """Clean database before each test to ensure isolation."""
        with self.app.app_context():
            db.session.query(Level).delete()
            db.session.commit()

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    def test_create_level(self):
        """Test creating a new level returns 201 and valid ID."""
        payload = {
            "description": "Beginner",
            "cosmetic": "Green badge",
            "min_xp": 0,
        }
        response = self.client.post("/api/level", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["message"], "Level created successfully")

    # ------------------------------------------------------------------ #
    # READ ALL
    # ------------------------------------------------------------------ #
    def test_get_all_levels(self):
        """Test retrieving all levels returns a list with expected content."""
        with self.app.app_context():
            level = Level(
                description="Test",
                cosmetic="x",
                min_xp=5,
                date_created=datetime.datetime.now(),
            )
            db.session.add(level)
            db.session.commit()

        response = self.client.get("/api/level")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["description"], "Test")

    # ------------------------------------------------------------------ #
    # READ ONE
    # ------------------------------------------------------------------ #
    def test_get_level_by_id(self):
        """Test retrieving a level by ID returns the correct record."""
        with self.app.app_context():
            level = Level(
                description="Solo",
                cosmetic="x",
                min_xp=10,
                date_created=datetime.datetime.now(),
            )
            db.session.add(level)
            db.session.commit()
            level_id = level.id

        response = self.client.get(f"/api/level/{level_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["id"], level_id)
        self.assertEqual(data["description"], "Solo")

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def test_update_level(self):
        """Test updating an existing level modifies its fields."""
        with self.app.app_context():
            level = Level(
                description="Old",
                cosmetic="x",
                min_xp=1,
                date_created=datetime.datetime.now(),
            )
            db.session.add(level)
            db.session.commit()
            level_id = level.id

        payload = {"description": "Updated", "min_xp": 15}
        response = self.client.put(f"/api/level/{level_id}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated succesfully", response.get_json()["message"])

        with self.app.app_context():
            updated = Level.query.get(level_id)
            self.assertIsNotNone(updated)
            updated = cast(Level, updated)
            self.assertEqual(updated.description, "Updated")
            self.assertEqual(updated.min_xp, 15)

    # ------------------------------------------------------------------ #
    # SOFT DELETE
    # ------------------------------------------------------------------ #
    def test_soft_delete_level(self):
        """Test soft-deleting a level sets the date_deleted timestamp."""
        with self.app.app_context():
            level = Level(
                description="To delete",
                cosmetic="y",
                min_xp=50,
                date_created=datetime.datetime.now(),
            )
            db.session.add(level)
            db.session.commit()
            level_id = level.id

        response = self.client.delete(f"/api/level/{level_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_json()["message"])

        with self.app.app_context():
            deleted = Level.query.get(level_id)
            self.assertIsNotNone(deleted)
            deleted = cast(Level, deleted)
            self.assertIsNotNone(deleted.date_deleted)

    # ------------------------------------------------------------------ #
    # HARD DELETE
    # ------------------------------------------------------------------ #
    def test_hard_delete_level(self):
        """Test hard-deleting a level removes it from the database."""
        with self.app.app_context():
            level = Level(
                description="Hard delete",
                cosmetic="z",
                min_xp=99,
                date_created=datetime.datetime.now(),
            )
            db.session.add(level)
            db.session.commit()
            level_id = level.id

        response = self.client.delete(f"/api/level/{level_id}/hard")
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            deleted = Level.query.get(level_id)
            self.assertIsNone(deleted)


if __name__ == "__main__":
    unittest.main()
