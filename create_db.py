# create_db.py
import os
from dotenv import load_dotenv
from app import app # Importa tu instancia de Flask desde app.py
from models import db, Pedido # Asegúrate de importar tus modelos aquí
from datetime import datetime, timedelta # Importar timedelta para fechas

# Cargar variables de entorno desde .env
# Es importante cargar las variables también en este script
load_dotenv()

# Configuración de la base de datos dentro del contexto de la aplicación
# Esto asegura que db.create_all() use la misma URI de DB que tu app principal
with app.app_context():
    # Asegúrate de que este script también use la variable de entorno
    # para conectarse a la misma base de datos PostgreSQL.
    # Si la variable DATABASE_URL no está definida en Render, esto usará el fallback.
    # Es CRÍTICO que el DATABASE_URL en Render esté configurado correctamente.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://basedatos_envios_khs_5200:3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176@dpg-d1pgve49c44c738k7j4g-a.oregon-postgres.render.com/basedatos_envios_khs_5200'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Mantener consistente con app.py

    # Inicializar la instancia de SQLAlchemy con la aplicación actual
    # Esto es crucial para que db.create_all() funcione correctamente en este contexto
    db.init_app(app)
    
    # Elimina todas las tablas existentes (¡CUIDADO! Esto borra todos los datos)
    # db.drop_all() 
    
    # Crea todas las tablas definidas en tus modelos
    db.create_all()
    print("Base de datos y tablas creadas exitosamente.")

    # Añadir 10 pedidos de prueba para verificar
    print("Añadiendo pedidos de prueba...")
    try:
        # Lista de estados posibles
        estados = ["Pendiente", "En Proceso", "Entregado", "Cancelado"]
        
        for i in range(1, 11): # Generar 10 pedidos
            pedido_id = f"PEDIDO-KHS-{i:03d}" # Formato PEDIDO-KHS-001, PEDIDO-KHS-002, etc.
            
            # Determinar el estado y la fecha de entrega
            estado_actual = estados[i % len(estados)] # Cicla a través de los estados
            
            fecha_impresion = datetime.now() - timedelta(days=i) # Fechas de impresión decrecientes
            
            # Si el estado es "Entregado", asigna una fecha de entrega y un nombre/firma
            if estado_actual == "Entregado":
                fecha_entrega = datetime.now() - timedelta(days=i-1) # Un día después de la impresión
                nombre_cliente = f"Cliente {i}"
                firma_base64 = f"data:image/png;base64,FIRMA_EJEMPLO_{i}"
                latitude = 19.2890 + (i * 0.01) # Latitudes de ejemplo
                longitude = -99.6530 + (i * 0.01) # Longitudes de ejemplo
            else:
                fecha_entrega = None
                nombre_cliente = None
                firma_base64 = None
                latitude = None
                longitude = None

            new_pedido = Pedido(
                pedido_id_unico=pedido_id,
                estado=estado_actual,
                cliente=f"Cliente de Prueba {i}",
                descripcion=f"Descripción de prueba para el pedido {i}. Producto X, Cantidad Y.",
                fecha_impresion=fecha_impresion,
                nombre_cliente=nombre_cliente,
                fecha_entrega=fecha_entrega,
                firma_base64=firma_base64,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(new_pedido)
        
        db.session.commit()
        print("10 pedidos de prueba añadidos exitosamente.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al añadir pedidos de prueba: {e}")
        # Opcional: Imprimir el traceback completo para depuración
        # import traceback
        # traceback.print_exc()
