"""SQLAlchemy ORM models for the application domain.

This module defines the core entities:
- Level: progression tiers (XP, description, cosmetics).
- Class: class/course grouping with capacity and suggested level.
- Exam: assessment entity linking coordinator, class and student.
- Exercise: single task/question within an exam (kept spelling to match DB).
- User: people in the system (coordinators, teachers, students).

Notes:
- Soft deletes are supported via the nullable ``date_deleted`` field.
- Many-to-many teacher assignments use the ``teacher_class`` association table.
"""

import datetime  # stdlib
from flask_sqlalchemy import SQLAlchemy  # third-party
from sqlalchemy import Enum  # third-party
from utils.types_enum import UserType  # local

db = SQLAlchemy()


class BaseModel(db.Model):
    """Abstract base model with common primary key and timestamps.

    Attributes:
        id: Surrogate integer primary key.
        date_created: Creation timestamp (server-side default).
        date_deleted: Soft-delete timestamp (null means active).
    """

    __abstract__ = True

    # Surrogate PK; widely used pattern with SQLAlchemy.
    id = db.Column(db.Integer, primary_key=True)

    # Using local time; consider UTC (datetime.datetime.utcnow) if you need
    # timezone-agnostic timestamps across deployments.
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)

    # Null when active; set to a timestamp to "soft delete" records.
    date_deleted = db.Column(db.DateTime, nullable=True, default=None)


# Association table for the many-to-many relation between teachers and classes.
# Kept as a plain Table to avoid a dedicated model class.
teacher_class = db.Table(
    "teacher_class",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "class_id",
        db.Integer,
        db.ForeignKey("class.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many between Exam and Exercise (exercise = "exercise type")
exam_exercise = db.Table(
    "exam_exercise",
    db.Column(
        "exam_id",
        db.Integer,
        db.ForeignKey("exam.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "exercise_id",
        db.Integer,
        db.ForeignKey("exercise.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Level(BaseModel):
    """Represents a progression level (tier) that a student can reach.

    Attributes:
        min_xp: Minimum XP required to reach/hold this level (unique).
        description: Human-readable label (unique).
        cosmetic: Optional cosmetic/metainfo (e.g., badge JSON or markdown).
        students: One-to-many: users enrolled at this level.
    """

    __tablename__ = "level"

    # Unique constraints help ensure a well-defined ladder.
    min_xp = db.Column(db.Integer, nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False, unique=True)

    # Text can store long free-form data; length is advisory in some backends.
    cosmetic = db.Column(db.Text(1024), nullable=True)

    # Back-populates User.student_level
    students = db.relationship("User", back_populates="student_level")


class Class(BaseModel):
    """Represents a class/course grouping.

    Attributes:
        class_code: Short unique code used to identify the class.
        description: Human-friendly name/description (unique).
        suggested_level: Guidance string (not a FK) for target level.
        max_capacity: Enrollment cap for the class.
        exams: One-to-many: exams tied to this class.
        students: One-to-many: users assigned to this class.
        teachers: Many-to-many: users who teach this class.
    """

    __tablename__ = "class"

    class_code = db.Column(db.String(16), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False, unique=True)

    # Kept as string; use a FK to Level if you want strict referential integrity.
    suggested_level = db.Column(db.String(255), nullable=False)

    max_capacity = db.Column(db.Integer, nullable=False)

    # Back-populates Exam.class_exam
    exams = db.relationship("Exam", back_populates="class_exam")

    # Back-populates User.student_class
    students = db.relationship("User", back_populates="student_class")

    # Many-to-many via the association table; back-populates User.teacher_classes
    teachers = db.relationship(
        "User",
        secondary=teacher_class,
        back_populates="teacher_classes",
    )


class Exam(BaseModel):
    """Represents an exam/assessment instance.

    Attributes:
        status: Current lifecycle state (e.g., 'draft', 'open', 'graded').
        notes: Optional free-form notes for the exam.
        coordinator_id: FK to the coordinating user.
        coordinator: Many-to-one: coordinating user (explicit FK to disambiguate).
        exercises: One-to-many: tasks/questions in this exam.
        class_id: FK to the class this exam belongs to.
        class_exam: Many-to-one: the owning Class.
        student_id: FK to the student taking this exam (if per-student).
        student_exam: Many-to-one: the student tied to this exam record.
    """

    __tablename__ = "exam"

    status = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text(1024), nullable=True)

    # Explicit foreign_keys avoids ambiguity because multiple FKs point to user.id.
    coordinator_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
    )
    coordinator_exam = db.relationship(
        "User",
        back_populates="coordinator_exams",
        foreign_keys="Exam.coordinator_id",
    )

    # Back-populates Exercise.exam
    exercises = db.relationship("Exercise", back_populates="exam")

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("class.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_exam = db.relationship("Class", back_populates="exams")

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
    )
    student_exam = db.relationship(
        "User",
        back_populates="student_exams",
        foreign_keys="Exam.student_id",
    )


class Exercise(db.Model):
    """Represents a type of exercise (exercise archetype), not a concrete
    question inside an exam.

    This model acts as a catalogue of exercise types that can be reused across
    many exams (many-to-many relationship).

    Attributes:
        id: Surrogate integer primary key.
        date_created: Creation timestamp (server-side default).
        date_deleted: Soft-delete timestamp (null means active).
        name: Human-readable unique name of the exercise type
              (e.g., "Cloze test with options").
        content_description: Long textual description explaining what this
              exercise type implies pedagogically and procedurally.
        exams: Many-to-many relationship with Exam via the exam_exercise table.
    """
    __tablename__ = "exercise"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Fecha de alta
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    # Fecha de baja lógica (soft delete)
    date_deleted = db.Column(db.DateTime, nullable=True)

    name = db.Column(db.String(255), nullable=False, unique=True)
    content_description = db.Column(db.Text, nullable=False)

    # Relación N:N con Exam
    exams = db.relationship(
        "Exam",
        secondary=exam_exercise,
        back_populates="exercise_types",
    )


class User(BaseModel):
    """Represents a person in the system.

    Attributes:
        name: First name.
        surname: Last name.
        email: Unique email used for login/identification.
        passwd: Hashed password (store hashes, never plain text).
        profile_picture: Optional URL or blob reference.
        type: Role enumeration (Coordinator/Teacher/Student).
        dni: National ID (string to preserve leading zeros).
        accumulated_xp: XP total for progression features.
        coordinator_exams: One-to-many: exams coordinated by this user.
        student_level_id/student_level: Optional link to Level.
        student_exams: One-to-many: exams taken by the student.
        student_class_id/student_class: Optional link to Class.
        teacher_classes: Many-to-many: classes this teacher teaches.
    """

    __tablename__ = "user"

    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    is_verified = db.Column(db.Boolean,nullable=False,default=False)
    passwd = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.Text(1024), nullable=True)

    # SQLAlchemy Enum bound to the Python Enum, persisted as strings by default.
    type = db.Column(Enum(UserType), nullable=False)

    # Keep as string to avoid dropping leading zeros/formatting characters.
    dni = db.Column(db.String(10), nullable=False)

    accumulated_xp = db.Column(db.Integer, nullable=True)

    # Back-populates Exam.coordinator
    coordinator_exams = db.relationship(
        "Exam",
        back_populates="coordinator_exam",
        foreign_keys="Exam.coordinator_id",
    )

    # Nullable to allow creating users before assigning a level.
    # If you want to enforce an initial level, set nullable=False and provide defaults.
    student_level_id = db.Column(
        db.Integer,
        db.ForeignKey("level.id", ondelete="CASCADE"),
        nullable=True,
    )
    student_level = db.relationship("Level", back_populates="students")

    # Back-populates Exam.student_exam
    student_exams = db.relationship(
        "Exam",
        back_populates="student_exam",
        foreign_keys="Exam.student_id",
    )

    # Nullable to support workflows where class assignment happens after signup.
    # Tighten by setting nullable=False if business rules require class on creation.
    student_class_id = db.Column(
        db.Integer,
        db.ForeignKey("class.id", ondelete="CASCADE"),
        nullable=True,
    )
    student_class = db.relationship("Class", back_populates="students")

    # Many-to-many via teacher_class; back-populates Class.teachers
    teacher_classes = db.relationship(
        "Class",
        secondary=teacher_class,
        back_populates="teachers",
    )
