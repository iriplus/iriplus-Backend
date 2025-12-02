"""Unit tests for CRUD operations of the User controller.

This test suite validates the creation, retrieval, updating, and deletion
of User entities using an in-memory SQLite database. It covers each user
type (Student, Teacher, Coordinator) and verifies response integrity and
database consistency.
"""

import unittest
from typing import cast
from flask import Flask
from orm_models import db, User
from utils.types_enum import UserType
from controllers import user_controller as uc


class TestUserCRUD(unittest.TestCase):
    """Test suite for CRUD operations of the User controller."""

    @classmethod
    def setUpClass(cls):
        """Set up a Flask app and in-memory database once for all tests."""
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        cls.app = app
        cls.client = app.test_client()

        with app.app_context():
            db.create_all()

            # Define wrapper functions mapping directly to controller logic.
            def create_student():
                return uc.create_user(UserType.STUDENT)

            def create_teacher():
                return uc.create_user(UserType.TEACHER)

            def create_coordinator():
                return uc.create_user(UserType.COORDINATOR)

            def get_all_students():
                return uc.get_all_users("Student")

            def get_all_teachers():
                return uc.get_all_users("Teacher")

            def get_all_coordinators():
                return uc.get_all_users("Coordinator")

            # Register routes manually for testing purposes.
            app.add_url_rule(
                "/api/user/student",
                "create_student",
                view_func=create_student,
                methods=["POST"],
            )
            app.add_url_rule(
                "/api/user/teacher",
                "create_teacher",
                view_func=create_teacher,
                methods=["POST"],
            )
            app.add_url_rule(
                "/api/user/coordinator",
                "create_coordinator",
                view_func=create_coordinator,
                methods=["POST"],
            )
            app.add_url_rule(
                "/api/user/<int:user_id>",
                "get_user",
                view_func=uc.get_user,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/user/student/all",
                "get_all_students",
                view_func=get_all_students,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/user/teacher/all",
                "get_all_teachers",
                view_func=get_all_teachers,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/user/coordinator/all",
                "get_all_coordinators",
                view_func=get_all_coordinators,
                methods=["GET"],
            )
            app.add_url_rule(
                "/api/user/<int:user_id>",
                "update_user",
                view_func=uc.update_user,
                methods=["PUT"],
            )
            app.add_url_rule(
                "/api/user/<int:user_id>",
                "delete_user",
                view_func=uc.delete_user,
                methods=["DELETE"],
            )

    def setUp(self):
        """Clean database before each test to ensure isolation."""
        with self.app.app_context():
            db.session.query(User).delete()
            db.session.commit()

    # ------------------------------------------------------------------ #
    # CREATE - STUDENT
    # ------------------------------------------------------------------ #
    def test_create_student(self):
        """Ensure a student can be created successfully."""
        payload = {
            "name": "John",
            "surname": "Doe",
            "email": "johndoe@example.com",
            "passwd": "password123",
            "dni": "12345678",
        }
        response = self.client.post("/api/user/student", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("user", data)
        self.assertEqual(data["message"], "User created successfully.")
        self.assertEqual(data["user"]["type"], "Student")

    def test_create_student_missing_fields(self):
        """Ensure missing required fields return HTTP 400."""
        payload = {"name": "Jane", "email": "jane@example.com"}
        response = self.client.post("/api/user/student", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Missing required fields", data["message"])

    # ------------------------------------------------------------------ #
    # CREATE - TEACHER
    # ------------------------------------------------------------------ #
    def test_create_teacher(self):
        """Ensure a teacher can be created successfully."""
        payload = {
            "name": "Angelina",
            "surname": "Jolie",
            "email": "angelinajolie@example.com",
            "passwd": "teacher1",
            "dni": "87654321",
        }
        response = self.client.post("/api/user/teacher", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["user"]["type"], "Teacher")
        self.assertEqual(data["user"]["name"], "Angelina")

    # ------------------------------------------------------------------ #
    # CREATE - COORDINATOR
    # ------------------------------------------------------------------ #
    def test_create_coordinator(self):
        """Ensure a coordinator can be created successfully."""
        payload = {
            "name": "Tom",
            "surname": "Cruise",
            "email": "tomcruise@example.com",
            "passwd": "coord1",
            "dni": "11223344",
        }
        response = self.client.post("/api/user/coordinator", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["user"]["type"], "Coordinator")
        self.assertEqual(data["user"]["surname"], "Cruise")

    # ------------------------------------------------------------------ #
    # CREATE - WITH OPTIONAL FIELDS
    # ------------------------------------------------------------------ #
    def test_create_student_with_optional_fields(self):
        """Ensure optional fields are stored correctly on creation."""
        payload = {
            "name": "Alice",
            "surname": "Smith",
            "email": "alice.smith@example.com",
            "passwd": "alice000",
            "dni": "99887766",
            "accumulated_xp": 100,
            "profile_picture": "https://example.com/alice.jpg",
            "student_level_id": 1,
            "student_class_id": 2,
        }
        response = self.client.post("/api/user/student", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["user"]["accumulated_xp"], 100)
        self.assertEqual(
            data["user"]["profile_picture"], "https://example.com/alice.jpg"
        )

    # ------------------------------------------------------------------ #
    # READ ONE
    # ------------------------------------------------------------------ #
    def test_get_user_by_id(self):
        """Ensure a user can be retrieved correctly by ID."""
        with self.app.app_context():
            user = User(
                name="Test",
                surname="User",
                email="test.user@example.com",
                passwd="hashedpass",
                dni="55443322",
                type=UserType.STUDENT,
                accumulated_xp=50,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = self.client.get(f"/api/user/{user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["id"], user_id)
        self.assertEqual(data["name"], "Test")

    def test_get_user_not_found(self):
        """Ensure retrieving a non-existent user returns 404."""
        response = self.client.get("/api/user/9999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["message"], "User not found.")

    # ------------------------------------------------------------------ #
    # READ ALL BY TYPE
    # ------------------------------------------------------------------ #
    def test_get_all_students(self):
        """Ensure all Student users are retrieved."""
        with self.app.app_context():
            student1 = User(
                name="Student1",
                surname="One",
                email="student1@example.com",
                passwd="pass1",
                dni="11111111",
                type=UserType.STUDENT,
            )
            student2 = User(
                name="Student2",
                surname="Two",
                email="student2@example.com",
                passwd="pass2",
                dni="22222222",
                type=UserType.STUDENT,
            )
            teacher = User(
                name="Teacher",
                surname="One",
                email="teacher@example.com",
                passwd="pass3",
                dni="33333333",
                type=UserType.TEACHER,
            )
            db.session.add_all([student1, student2, teacher])
            db.session.commit()

        response = self.client.get("/api/user/student/all")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertTrue(all(user["type"] == "Student" for user in data))

    def test_get_all_teachers(self):
        """Ensure all Teacher users are retrieved."""
        with self.app.app_context():
            teacher = User(
                name="TeacherName",
                surname="TeacherSurname",
                email="teacher@example.com",
                passwd="teachpass",
                dni="44444444",
                type=UserType.TEACHER,
            )
            db.session.add(teacher)
            db.session.commit()

        response = self.client.get("/api/user/teacher/all")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["type"], "Teacher")

    def test_get_all_users_empty(self):
        """Ensure empty user lists return 404."""
        response = self.client.get("/api/user/coordinator/all")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn("No coordinators found", data["message"])

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def test_update_user(self):
        """Ensure user fields are updated successfully."""
        with self.app.app_context():
            user = User(
                name="OldName",
                surname="OldSurname",
                email="old@example.com",
                passwd="oldpass",
                dni="66666666",
                type=UserType.STUDENT,
                accumulated_xp=0,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        payload = {
            "name": "NewName",
            "accumulated_xp": 200,
            "profile_picture": "https://example.com/new.jpg",
        }
        response = self.client.put(f"/api/user/{user_id}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated successfully", response.get_json()["message"])

        with self.app.app_context():
            updated = cast(User, User.query.get(user_id))
            self.assertEqual(updated.name, "NewName")
            self.assertEqual(updated.accumulated_xp, 200)
            self.assertEqual(updated.profile_picture, "https://example.com/new.jpg")
            self.assertEqual(updated.email, "old@example.com")

    def test_update_user_not_found(self):
        """Ensure updating a non-existent user returns 404."""
        payload = {"name": "NewName"}
        response = self.client.put("/api/user/9999", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_update_user_invalid_json(self):
        """Ensure invalid JSON input returns 400."""
        with self.app.app_context():
            user = User(
                name="Test",
                surname="User",
                email="test@example.com",
                passwd="pass",
                dni="77777777",
                type=UserType.STUDENT,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = self.client.put(
            f"/api/user/{user_id}", data="not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------ #
    # DELETE
    # ------------------------------------------------------------------ #
    def test_delete_user(self):
        """Ensure a user can be deleted successfully."""
        with self.app.app_context():
            user = User(
                name="ToDelete",
                surname="User",
                email="delete@example.com",
                passwd="pass",
                dni="88888888",
                type=UserType.COORDINATOR,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = self.client.delete(f"/api/user/{user_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_json()["message"])

        with self.app.app_context():
            deleted = User.query.get(user_id)
            self.assertIsNone(deleted)

    def test_delete_user_not_found(self):
        """Ensure deleting a non-existent user returns 404."""
        response = self.client.delete("/api/user/9999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["message"], "User not found.")


if __name__ == "__main__":
    unittest.main()
