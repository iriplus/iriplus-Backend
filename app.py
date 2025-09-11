from flask import Flask  # API REST en Python
from orm_models import db  # tu SQLAlchemy
import os
from dotenv import load_dotenv

# Cargar variables de entorno según el entorno
env_name = os.getenv("ENVIRONMENT", "dev")

if env_name == "production":
    load_dotenv(".env.production")
elif env_name == "testing":
    load_dotenv(".env.testing")
else:
    load_dotenv(".env.dev")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Crear la app Flask
app = Flask(__name__)

# Configuración de la BD
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Vincular SQLAlchemy con la app
db.init_app(app)

# Crear tablas dentro del contexto de la app
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente")


