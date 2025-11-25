"""Main Flask application setup.

This script initializes the Flask app, loads environment variables based on
the current environment, configures the database connection, and registers
blueprints for modular routes.

Run this file directly to start the development server.
"""

import os
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from orm_models import db
from routes.level_routes import level_bp
from routes.class_routes import class_bp
from routes.user_routes import user_bp
from routes.auth_routes import auth_bp
from routes.exam_routes import exam_bp
from routes.exercise_routes import exercise_bp


# ----------------------------------------------------------------------------
# Environment configuration
# ----------------------------------------------------------------------------

env_name = os.getenv("ENVIRONMENT", "dev")

if env_name == "production":
    load_dotenv(".env.production")
elif env_name == "testing":
    load_dotenv(".env.testing")
else:
    load_dotenv(".env.dev")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")   # para CORS
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")           # obligatorio


# ----------------------------------------------------------------------------
# Flask app setup
# ----------------------------------------------------------------------------

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT CONFIG - usando cookies HttpOnly
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_HTTPONLY"] = True
app.config["JWT_COOKIE_SECURE"] = False if env_name == "dev" else True
app.config["JWT_COOKIE_SAMESITE"] = "None" if env_name == "production" else "Lax"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
# si querés protección CSRF está integrada, luego se habilita en el controller si se desea
# app.config["JWT_COOKIE_CSRF_PROTECT"] = True

# permitir peticiones del frontend con cookies
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# inicializar SQLAlchemy y JWT
db.init_app(app)
jwt = JWTManager(app)


# ----------------------------------------------------------------------------
# Register blueprints
# ----------------------------------------------------------------------------
app.register_blueprint(level_bp)
app.register_blueprint(class_bp)
app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(exercise_bp)


# ----------------------------------------------------------------------------
# Database init
# ----------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully")


# ----------------------------------------------------------------------------
# Run server
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug = env_name == "dev")
