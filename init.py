# The init file only has to be run whern changed to the DB stricture are made.
from app import app, db 
with app.app_context():
    db.create_all()
    print("Tablas creadas correctamente.")