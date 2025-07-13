# create_db.py
from app import app
from models import db, Pedido # Asegúrate de importar tus modelos aquí

with app.app_context():
    # Elimina todas las tablas existentes (¡CUIDADO! Esto borra todos los datos)
    # db.drop_all() 
    
    # Crea todas las tablas definidas en tus modelos
    db.create_all()
    print("Base de datos y tablas creadas exitosamente.")
