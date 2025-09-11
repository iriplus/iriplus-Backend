from flask_sqlalchemy import SQLAlchemy
import datetime
import enum
from sqlalchemy import Enum

db = SQLAlchemy()

class UserType(enum.Enum):
    coordinator = "Coordinator"
    teacher = "Teacher"
    student = "Student"


class BaseModel(db.Model):
    __abstract__= True
    id = db.Column(db.Integer, primary_key=True) 
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)
    date_deleted = db.Column(db.DateTime, nullable=True)


class Level(BaseModel):
    min_xp = db.Column(db.Integer, nullable = False, unique = True)
    description = db.Column(db.String(255), nullable = False, unique = True)
    cosmetic = db.Column(db.Text, nullable = True, unique = True)

class Class(BaseModel):
    class_code = db.Column(db.Column(db.String(16)), nullable = False, unique = True)

class User(BaseModel):
    name = db.Column(db.String(255), nullable = False)
    surname = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True),
    passwd = db.Column(db.String(255), nullable = False)
    profile_picture = db.Column(db.Text, nullable = True)
    type = db.Column(Enum(UserType), nullable = False)
    dni = db.Column(db.String(10), nullable = False)
    accumulated_xp = db.Column(db.Integer, nullable = True)

