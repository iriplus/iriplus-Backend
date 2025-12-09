"""Unit tests for CRUD operations of the Class controller.

This test suite validates the behavior of all endpoints defined in
class_controller.py using an in-memory SQLite database.
"""

import unittest
import datetime
from typing import cast
from flask import Flask
from orm_models import db, Class
from controllers import class_controller as cc


class TestClassCRUD(unittest.TestCase):
    """Test suite for CRUD operations of the Class controller."""

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

            # Register controller functions as Flask routes for testing.
            app.add_url_rule("/api/class", view_func=cc.create_class, methods=["POST"])
            app.add_url_rule("/api/class", view_func=cc.get_all_classes, methods=["GET"])
            app.add_url_rule(
                "/api/class/<int:class_id>",
                view_func=cc.get_class_by_id,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/class/<int:class_id>",
                view_func=cc.update_class,
                methods=["PUT"],
            )
            app.add_url_rule(
                "/api/class/<int:class_id>",
                view_func=cc.delete_class,
                methods=["DELETE"],
            )

    def setUp(self):
        """Reset the database before each individual test."""
        with self.app.app_context():
            db.session.query(Class).delete()
            db.session.commit()

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    def test_create_class(self):
        """Ensure that a new Class record can be created successfully."""
        payload = {
            "class_code": "ENG101",
            "description": "Basic English",
            "suggested_level": "Beginner",
            "max_capacity": 20,
        }

        response = self.client.post("/api/class", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["message"], "Class created successfully")

    # ------------------------------------------------------------------ #
    # READ ALL
    # ------------------------------------------------------------------ #
    def test_get_all_classes(self):
        """Ensure that all non-deleted Class records are retrieved."""
        with self.app.app_context():
            clazz = Class(
                class_code="ENG201",
                description="English Intro",
                suggested_level="Intermediate",
                max_capacity=15,
                date_created=datetime.datetime.now(),
            )
            db.session.add(clazz)
            db.session.commit()

        response = self.client.get("/api/class")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["class_code"], "ENG201")

    # ------------------------------------------------------------------ #
    # READ ONE
    # ------------------------------------------------------------------ #
    def test_get_class_by_id(self):
        """Ensure that a specific Class can be retrieved by ID."""
        with self.app.app_context():
            clazz = Class(
                class_code="USENG01",
                description="Intro to US English",
                suggested_level="Beginner",
                max_capacity=20,
                date_created=datetime.datetime.now(),
            )
            db.session.add(clazz)
            db.session.commit()
            class_id = clazz.id

        response = self.client.get(f"/api/class/{class_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["id"], class_id)
        self.assertEqual(data["description"], "Intro to US English")

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def test_update_class(self):
        """Ensure that an existing Class record can be updated."""
        with self.app.app_context():
            clazz = Class(
                class_code="ENG1",
                description="English I",
                suggested_level="A1",
                max_capacity=20,
                date_created=datetime.datetime.now(),
            )
            db.session.add(clazz)
            db.session.commit()
            class_id = clazz.id

        payload = {"description": "English I Updated", "max_capacity": 25}

        response = self.client.put(f"/api/class/{class_id}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully", response.get_json()["message"])

        with self.app.app_context():
            updated = cast(Class, Class.query.get(class_id))
            self.assertEqual(updated.description, "English I Updated")
            self.assertEqual(updated.max_capacity, 25)

    # ------------------------------------------------------------------ #
    # SOFT DELETE
    # ------------------------------------------------------------------ #
    def test_soft_delete_class(self):
        """Ensure that deleting a Class sets its date_deleted timestamp."""
        with self.app.app_context():
            clazz = Class(
                class_code="ENG301",
                description="English 301",
                suggested_level="Any",
                max_capacity=10,
                date_created=datetime.datetime.now(),
            )
            db.session.add(clazz)
            db.session.commit()
            class_id = clazz.id

        response = self.client.delete(f"/api/class/{class_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_json()["message"])

        with self.app.app_context():
            deleted = Class.query.get(class_id)
            self.assertIsNotNone(deleted)
            # date_deleted should be populated (soft delete verification).
            self.assertIsNotNone(deleted.date_deleted)  # type: ignore


if __name__ == "__main__":
    unittest.main()
