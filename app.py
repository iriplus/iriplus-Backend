"""Main Flask application setup.

This script initializes the Flask app, loads environment variables based on
the current environment, configures the database connection, and registers
blueprints for modular routes.

Run this file directly to start the development server.
"""

import os
from flask import Flask
from dotenv import load_dotenv
from orm_models import db
from routes.level_routes import level_bp
from routes.class_routes import class_bp
from routes.exam_routes import exam_bp

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

# Detect current environment (defaults to 'dev' if ENVIRONMENT is not set).
env_name = os.getenv("ENVIRONMENT", "dev")

# Load environment-specific variables from .env files.
if env_name == "production":
    load_dotenv(".env.production")
elif env_name == "testing":
    load_dotenv(".env.testing")
else:
    load_dotenv(".env.dev")

# Database connection parameters loaded from environment variables.
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")  # Currently unused in connection string
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ---------------------------------------------------------------------------
# Flask app and database setup
# ---------------------------------------------------------------------------

# Create the Flask application instance.
app = Flask(__name__)

# Configure SQLAlchemy connection string (MySQL + PyMySQL dialect).
# Note: DB_PORT is not interpolated here; add it if your DB runs on non-default port.
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)

# Disable modification tracking to reduce overhead (recommended).
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind SQLAlchemy to the Flask app.
db.init_app(app)

# Register modular blueprints (routes are organized by domain).
app.register_blueprint(level_bp)
app.register_blueprint(class_bp)
app.register_blueprint(exam_bp)

# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

# Create tables automatically within app context if they do not exist.
# Consider using Alembic migrations for production deployments instead.
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# When run directly, start the Flask development server.
if __name__ == "__main__":
    app.run(debug=True)
