from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Pedido(db.Model):
    __tablename__ = 'pedido' # Asegura que el nombre de la tabla sea 'pedido'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id_unico = db.Column(db.String(120), unique=True, nullable=False, index=True)
    estado = db.Column(db.String(50), nullable=False, default="En ruta")
    cliente = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_impresion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Nuevas columnas para la confirmación de entrega
    nombre_cliente = db.Column(db.String(255), nullable=True) # Nombre de quien recibe
    fecha_entrega = db.Column(db.DateTime, nullable=True)     # Fecha y hora de entrega
    firma_base64 = db.Column(db.Text, nullable=True)          # Firma en base64
    latitude = db.Column(db.String(50), nullable=True)        # Latitud de la entrega
    longitude = db.Column(db.String(50), nullable=True)       # Longitud de la entrega

    def __repr__(self):
        return f"<Pedido {self.pedido_id_unico}>"
