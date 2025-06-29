from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Este es el ID único del pedido que pasas por el QR
    pedido_id_unico = db.Column(db.String(80), unique=True, nullable=False)
    nombre_cliente = db.Column(db.String(120), nullable=True)
    firma_base64 = db.Column(db.Text, nullable=True) # La firma se guardará como texto Base64
    fecha_entrega = db.Column(db.DateTime, nullable=True, default=None)
    estado = db.Column(db.String(50), default="En ruta") # Ej: "En ruta", "Entregado", "Pendiente"
    # Puedes añadir más campos aquí: direccion, productos, etc.

    def __repr__(self):
        return f"<Pedido {self.pedido_id_unico} - Estado: {self.estado}>"