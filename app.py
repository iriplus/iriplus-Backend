import os
from flask import Flask
from orm_models import db
from dotenv import load_dotenv
from routes.level_routes import level_bp


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

app.register_blueprint(level_bp)

# Crear tablas dentro del contexto de la app
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente")

if __name__ == "__main__":
    app.run(debug=True)
