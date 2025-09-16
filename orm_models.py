from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy import Enum
from user_type_enum import UserType

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key = True) 
    date_created = db.Column(db.DateTime, default = datetime.datetime.now)
    date_deleted = db.Column(db.DateTime, nullable = True)

teacher_class = db.Table(
    "teacher_class",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    db.Column("class_id", db.Integer, db.ForeignKey("class.id", ondelete="CASCADE"), primary_key=True),
)

class Level(BaseModel):
    __tablename__ = "level"
    min_xp = db.Column(db.Integer, nullable = False, unique = True)
    description = db.Column(db.String(255), nullable = False, unique = True)
    cosmetic = db.Column(db.Text(1024), nullable = True, )

    students = db.relationship("User", back_populates = "student_level")

class Class(BaseModel):
    __tablename__ = 'class'
    class_code = db.Column(db.String(16), nullable = False, unique = True)
    description = db.Column(db.String(255), nullable = False, unique = True)
    suggested_level = db.Column(db.String(255), nullable = False)
    max_capacity = db.Column(db.Integer, nullable = False)

    exams = db.relationship("Exam", back_populates = "class_exam")

    students = db.relationship("User", back_populates = "student_class")

    teachers = db.relationship("User",secondary = teacher_class,back_populates = "teacher_classes")

class Exam(BaseModel):
    __tablename__ = 'exam'
    status = db.Column(db.String(255), nullable = False)
    notes = db.Column(db.Text(1024), nullable = True)
    
    coordinator_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete = "CASCADE"), nullable = True)
    coordinator = db.relationship("User", back_populates = "coordinator_exams", foreign_keys="Exam.coordinator_id")

    excercises = db.relationship("Excercise", back_populates = "exam")

    class_id = db.Column(db.Integer, db.ForeignKey("class.id", ondelete = "CASCADE"), nullable = True)
    class_exam = db.relationship("Class", back_populates = "exams") 

    student_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete = "CASCADE"), nullable = True)
    student_exam = db.relationship("User", back_populates = "student_exams", foreign_keys="Exam.student_id",)

class Excercise(BaseModel):
    __tablename__ = 'excercise'
    type = db.Column(db.String(255), nullable = False)
    content = db.Column(db.Text(1024), nullable = False)
    rubric = db.Column(db.String(255), nullable = False)
    key = db.Column(db.String(255), nullable = False)

    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id", ondelete = "CASCADE"), nullable = False)
    exam = db.relationship("Exam", back_populates = "excercises")

class User(BaseModel):
    __tablename__ = 'user'
    name = db.Column(db.String(255), nullable = False)
    surname = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True)
    passwd = db.Column(db.String(255), nullable = False)
    profile_picture = db.Column(db.Text(1024), nullable = True)
    type = db.Column(Enum(UserType), nullable = False)
    dni = db.Column(db.String(10), nullable = False)
    accumulated_xp = db.Column(db.Integer, nullable = True)

    coordinator_exams = db.relationship("Exam",back_populates = "coordinator", foreign_keys="Exam.coordinator_id")

    student_level_id = db.Column(db.Integer, db.ForeignKey("level.id", ondelete = "CASCADE"), nullable = True)
    student_level = db.relationship("Level", back_populates = "students")

    student_exams = db.relationship("Exam", back_populates = "student_exam", foreign_keys="Exam.student_id")

    student_class_id = db.Column(db.Integer, db.ForeignKey("class.id", ondelete = "CASCADE"), nullable = True)
    student_class = db.relationship("Class", back_populates = "students")

    teacher_classes = db.relationship("Class", secondary = teacher_class, back_populates = "teachers")
