from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy import Enum
from user_type_enum import UserType

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__= True
    id = db.Column(db.Integer, primary_key=True) 
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)
    date_deleted = db.Column(db.DateTime, nullable=True)


class Level(BaseModel):
    __tablename__ = "level"
    min_xp = db.Column(db.Integer, nullable = False, unique = True)
    description = db.Column(db.String(255), nullable = False, unique = True)
    cosmetic = db.Column(db.Text, nullable = True, unique = True)

class Class(BaseModel):
    __tablename__ = 'class'
    class_code = db.Column(db.String(16), nullable = False, unique = True)
    description = db.Column(db.String(255), nullable = False, unique = True)
    suggested_level = db.Column(db.String(255), nullable = False)
    max_capacity = db.Column(db.Integer, nullable = False)

class Exam(BaseModel):
    __tablename__ = 'exam'
    status = db.Column(db.String(255), nullable = False)
    notes = db.Column(db.Text, nullable = True)
    
    coordinator_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    coordinator = db.relationship("User", back_populates = "coordinator_exams")

    excercises = db.relationship("Excercise", back_populates = "exam")

class Excercise(BaseModel):
    __tablename__ = 'excercise'
    type = db.Column(db.String(255), nullable = False)
    content = db.Column(db.Text, nullable = False)
    rubric = db.Column(db.String(255), nullable = False)
    key = db.Column(db.String(255), nullable = False)

    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id", ondelete="CASCADE", nullable = False))
    exam = db.relationship("Exam", back_populates = "excercises")

class User(BaseModel):
    __tablename__ = 'user'
    name = db.Column(db.String(255), nullable = False)
    surname = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True)
    passwd = db.Column(db.String(255), nullable = False)
    profile_picture = db.Column(db.Text, nullable = True)
    type = db.Column(Enum(UserType), nullable = False)
    dni = db.Column(db.String(10), nullable = False)
    accumulated_xp = db.Column(db.Integer, nullable = True)

    coordinator_exams = db.relationship("Exam",back_populates="coordinator")
