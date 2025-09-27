"""Application entry-point for database initialization.

This script ensures that all tables defined in the ORM models are created
when the application starts (if they do not already exist).
"""

from app import app, db

# Ensure the database operations run within the Flask application context.
with app.app_context():
    # Create all tables defined by SQLAlchemy models (no-op if they exist).
    db.create_all()

    # Helpful message for developers/admins when initializing the DB.
    print("Tables created successfully.")
