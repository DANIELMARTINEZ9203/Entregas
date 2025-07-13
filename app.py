# app.py
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
# Importar db y Pedido desde models.py - asumiendo que Pedido está definido allí
from models import db, Pedido 
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
# Asegúrate de que tu archivo .env no sobrescriba esto con una URL de SQLite si no quieres usar SQLite localmente.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://basedatos_envios_khs_5200:3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176@dpg-d1pgve49c44c738k7j4g-a.oregon-postgres.render.com/basedatos_envios_khs_5200')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176') # ¡CAMBIA ESTO EN PRODUCCIÓN!

# Línea de depuración para ver la URI de la base de datos
print(f"DEBUG: SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Inicializar db con la aplicación Flask
db.init_app(app)

# Crear la base de datos si no existe
with app.app_context():
    try:
        db.create_all()
        print("Base de datos creada/actualizada si no existía.")

        # Opcional: Añadir algunos pedidos de prueba si la BD está vacía
        if Pedido.query.count() == 0:
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-001", estado="En ruta", cliente="KHS Mexico S.A. de C.V.", descripcion="Bomba de Agua", fecha_impresion=datetime(2024, 7, 10, 10, 0, 0)))
            # Para PEDIDO-KHS-002, lo inicializamos como "Entregado" con algunos datos para la prueba
            db.session.add(Pedido(
                pedido_id_unico="PEDIDO-KHS-002",
                estado="Entregado",
                cliente="Cliente Ejemplo S.A.",
                descripcion="Componentes Electrónicos",
                fecha_impresion=datetime(2024, 7, 11, 14, 30, 0),
                nombre_cliente="Juan Perez", # Datos de prueba para un pedido entregado
                fecha_entrega=datetime(2024, 7, 11, 15, 0, 0),
                firma_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", # Pequeña imagen base64 de 1x1 pixel
                latitude="19.2833", # Latitud de ejemplo
                longitude="-99.1333" # Longitud de ejemplo
            ))
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-003", estado="En ruta", cliente="Proveedor Industrial", descripcion="Refacciones Varias", fecha_impresion=datetime(2024, 7, 12, 9, 15, 0)))
            db.session.commit()
            print("Pedidos de prueba añadidos a la base de datos.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar o inicializar la base de datos: {e}")
        print("Asegúrate de que la URL de la base de datos sea correcta y accesible.")


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
        # Limpiar cualquier mensaje flash existente antes de mostrar uno nuevo
        session.pop('_flashes', None)
        
        # Flashear un mensaje específico para este pedido ya entregado
        formatted_fecha_entrega = pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S") if pedido.fecha_entrega else 'N/A'
        flash(f'El pedido **{pedido_id_unico}** ya ha sido marcado como entregado el **{formatted_fecha_entrega}**.', 'info')
        
        # Preparar los datos para exito.html, asegurando que no sean None
        nombre_cliente_display = pedido.nombre_cliente if pedido.nombre_cliente else 'N/A'
        firma_base64_display = pedido.firma_base64 if pedido.firma_base64 else ''
        latitude_display = pedido.latitude if pedido.latitude else ''
        longitude_display = pedido.longitude if pedido.longitude else ''

        try:
            return render_template('exito.html',
                                     pedido_id=pedido_id_unico,
                                     mensaje="Este pedido ya ha sido entregado.",
                                     nombre_cliente=nombre_cliente_display,
                                     fecha_entrega=formatted_fecha_entrega,
                                     firma_base64=firma_base64_display,
                                     latitude=latitude_display,
                                     longitude=longitude_display)
        except Exception as e:
            print(f"ERROR: Error al renderizar exito.html para pedido {pedido_id_unico}: {e}")
            flash(f'Error interno al mostrar los detalles del pedido: {e}', 'error')
            return redirect(url_for('error_page'))


    # Procesar el formulario cuando se envía (método POST)
    if request.method == 'POST':
        nombre_cliente = request.form['nombre_cliente']
        firma_base64 = request.form['firma_data']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Validar que los campos requeridos no estén vacíos
        if not nombre_cliente or not firma_base64:
            flash('Por favor, ingrese su nombre y firme para confirmar la entrega.', 'error')
            return render_template('confirmar_entrega.html',
                                   pedido_id=pedido_id_unico,
                                   pedido=pedido)
        
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
            # Limpiar cualquier mensaje flash existente antes de flashear el de éxito
            session.pop('_flashes', None)
            flash('¡Entrega confirmada con éxito!', 'success')
            
            # Redirigir a una página de éxito o mostrar el resultado
            formatted_fecha_entrega = pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S") if pedido.fecha_entrega else 'N/A'
            return render_template('exito.html',
                                     pedido_id=pedido_id_unico,
                                     nombre_cliente=nombre_cliente,
                                     fecha_entrega=formatted_fecha_entrega,
                                     firma_base64=firma_base64,
                                     latitude=latitude,
                                     longitude=longitude)
        except Exception as e:
            # En caso de error, revertir la transacción y mostrar un mensaje
            db.session.rollback()
            flash(f'Error al guardar la confirmación: **{e}**', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

    # Mostrar el formulario de confirmación de entrega (método GET)
    # Limpiar cualquier mensaje flash existente cuando se carga el formulario
    # para un pedido que no ha sido entregado aún.
    session.pop('_flashes', None)
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
