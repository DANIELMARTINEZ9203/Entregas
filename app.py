# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://basedatos_envios_khs_5200:3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176@dpg-d1pgve49c44c738k7j4g-a.oregon-postgres.render.com/basedatos_envios_khs_5200')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una_clave_secreta_muy_segura_aqui') # ¡CAMBIA ESTO EN PRODUCCIÓN!

db = SQLAlchemy(app)

# --- Modelo de Base de Datos ---
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id_unico = db.Column(db.String(80), unique=True, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="Pendiente")
    nombre_cliente = db.Column(db.String(120), nullable=True)
    firma_base64 = db.Column(db.Text, nullable=True)
    fecha_entrega = db.Column(db.DateTime, nullable=True)
    # Campos adicionales para la información del pedido que se muestra en el HTML
    cliente = db.Column(db.String(120), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_impresion = db.Column(db.DateTime, nullable=True, default=datetime.now)
    # Campos para la ubicación
    latitude = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Pedido {self.pedido_id_unico}>'

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

    # Opcional: Añadir algunos pedidos de prueba si la BD está vacía
    if Pedido.query.count() == 0:
        db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-001", estado="En ruta", cliente="KHS Mexico S.A. de C.V.", descripcion="Bomba de Agua", fecha_impresion=datetime(2024, 7, 10, 10, 0, 0)))
        db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-002", estado="En ruta", cliente="Cliente Ejemplo S.A.", descripcion="Componentes Electrónicos", fecha_impresion=datetime(2024, 7, 11, 14, 30, 0)))
        db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-003", estado="En ruta", cliente="Proveedor Industrial", descripcion="Refacciones Varias", fecha_impresion=datetime(2024, 7, 12, 9, 15, 0)))
        db.session.commit()
        print("Pedidos de prueba añadidos a la base de datos.")

# --- Rutas de la Aplicación ---
@app.route('/')
def index():
    """Ruta principal que muestra un mensaje de bienvenida."""
    return "Bienvenido al sistema de confirmación de entregas de KHS México."

@app.route('/confirmar_entrega', methods=['GET', 'POST'])
def confirmar_entrega():
    """
    Maneja la visualización del formulario de confirmación de entrega
    y el procesamiento de la información enviada.
    """
    # Obtener el ID del pedido de los parámetros de la URL
    pedido_id_unico = request.args.get('pedido_id')

    if not pedido_id_unico:
        flash('ID de pedido no proporcionado.', 'error')
        return redirect(url_for('error_page'))

    # Buscar el pedido en la base de datos
    pedido = Pedido.query.filter_by(pedido_id_unico=pedido_id_unico).first()

    if not pedido:
        flash(f'Pedido con ID **{pedido_id_unico}** no encontrado.', 'error')
        return redirect(url_for('error_page'))

    # Si el pedido ya está entregado, mostrar mensaje y detalles
    if pedido.estado == "Entregado":
        flash(f'El pedido **{pedido_id_unico}** ya ha sido marcado como entregado el **{pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S")}**.', 'info')
        return render_template('exito.html',
                               pedido_id=pedido_id_unico,
                               mensaje="Este pedido ya ha sido entregado.",
                               nombre_cliente=pedido.nombre_cliente,
                               fecha_entrega=pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S"),
                               firma_base64=pedido.firma_base64,
                               latitude=pedido.latitude,
                               longitude=pedido.longitude)

    # Procesar el formulario cuando se envía (método POST)
    if request.method == 'POST':
        nombre_cliente = request.form['nombre_cliente']
        firma_base64 = request.form['firma_data']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Validar que los campos requeridos no estén vacíos
        if not nombre_cliente or not firma_base64:
            flash('Por favor, ingrese su nombre y firme para confirmar la entrega.', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

        # Actualizar los datos del pedido
        pedido.nombre_cliente = nombre_cliente
        pedido.firma_base64 = firma_base64
        pedido.fecha_entrega = datetime.now()
        pedido.estado = "Entregado"
        pedido.latitude = latitude
        pedido.longitude = longitude

        try:
            # Guardar los cambios en la base de datos
            db.session.commit()
            flash('¡Entrega confirmada con éxito!', 'success')
            # Redirigir a una página de éxito o mostrar el resultado
            return render_template('exito.html',
                                   pedido_id=pedido_id_unico,
                                   nombre_cliente=nombre_cliente,
                                   fecha_entrega=pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S"),
                                   firma_base64=firma_base64,
                                   latitude=latitude,
                                   longitude=longitude)
        except Exception as e:
            # En caso de error, revertir la transacción y mostrar un mensaje
            db.session.rollback()
            flash(f'Error al guardar la confirmación: **{e}**', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

    # Mostrar el formulario de confirmación de entrega (método GET)
    return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

@app.route('/error')
def error_page():
    """Página de error genérica."""
    return render_template('error.html')

if __name__ == '__main__':
    # Ejecutar la aplicación Flask
    # 'debug=True' solo para desarrollo, ¡cambiar a False en producción!
    # 'host='0.0.0.0'' para que sea accesible desde otras máquinas en la red local
    app.run(debug=True, host='0.0.0.0')
