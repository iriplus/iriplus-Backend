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
from flasgger import Swagger
from orm_models import db
from routes.level_routes import level_bp
from routes.class_routes import class_bp
from routes.user_routes import user_bp
from routes.auth_routes import auth_bp
from routes.exam_routes import exam_bp
from routes.test_mail import test_mail_bp
from routes.exercise_routes import exercise_bp
from swagger.config import swagger_config
from swagger.template import swagger_template
from extensions.mail_extension import mail
from extensions.redis_extension import get_redis_client


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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")   # for CORS
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")           # mandatory

# mail credenciales desde .env
SECRET_KEY = os.getenv("SECRET_KEY")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

# ----------------------------------------------------------------------------
# Flask app setup
# ----------------------------------------------------------------------------

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT CONFIG - using cookies HttpOnly
# JWT CONFIG
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_HTTPONLY"] = True
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_DOMAIN"] = None
app.config["JWT_SESSION_COOKIE"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
# if CSRF protection is wanted it is integrated, you have to activate it on the controller if you wish to
# app.config["JWT_COOKIE_CSRF_PROTECT"] = True

# allow frontend petitions with cookies

# MAIL CONFIG
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USE_SSL"] = MAIL_USE_SSL
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER

# REDIS CONFIG
app.extensions["redis_client"] = get_redis_client()

# allow frontend cookies
CORS(
    app,
    supports_credentials=True,
    origins=[
        FRONTEND_URL
    ],
)

# initialize SQLAlchemy and JWT
# initialize libs
db.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)

# ----------------------------------------------------------------------------
# Swagger/OpenAPI configuration
# ----------------------------------------------------------------------------

Swagger(app, config=swagger_config, template=swagger_template)

# ----------------------------------------------------------------------------
# Register blueprints
# ----------------------------------------------------------------------------
app.register_blueprint(level_bp)
app.register_blueprint(class_bp)
app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(exercise_bp)
app.register_blueprint(test_mail_bp)



# ----------------------------------------------------------------------------
# Database init
# ----------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully")


# ----------------------------------------------------------------------------
# Run server
# ----------------------------------------------------------------------------
@app.route("/")
def root():
    """
    This function returns a message when loading the '/' route so that it erases noise in the logs
    """
    return {"message": "IRI+ API running"}, 200

if __name__ == "__main__":
    app.run(debug = env_name == "dev")
