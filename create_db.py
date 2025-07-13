# create_db.py
from app import app
from models import db, Pedido # Asegúrate de importar tus modelos aquí

with app.app_context():
    # Elimina todas las tablas existentes (¡CUIDADO! Esto borra todos los datos)
    # db.drop_all() 
    
    # Crea todas las tablas definidas en tus modelos
    db.create_all()
    print("Base de datos y tablas creadas exitosamente.")

    # Opcional: Añadir un pedido de prueba para verificar
     from datetime import datetime
     new_pedido = Pedido(
         pedido_id_unico="PEDIDO-KHS-001",
         estado="Pendiente",
         cliente="Cliente de Prueba",
         descripcion="Descripción de prueba",
         fecha_impresion=datetime.now(),
         nombre_cliente=None,
         fecha_entrega=None,
         firma_base64=None,
         latitude=None,
         longitude=None
     )
     db.session.add(new_pedido)
     db.session.commit()
     print("Pedido de prueba añadido.")
