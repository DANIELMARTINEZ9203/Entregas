# app.py
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import db, Pedido 
import os
from dotenv import load_dotenv
from datetime import datetime
import traceback # Importar traceback para depuración

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://basedatos_envios_khs_5200:3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176@dpg-d1pgve49c44c738k7j4g-a.oregon-postgres.render.com/basedatos_envios_khs_5200')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176') # ¡CAMBIA ESTO EN PRODUCCIÓN!

print(f"DEBUG: SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

db.init_app(app)

# --- Ruta para inicializar la base de datos (¡SOLO PARA DESARROLLO/PRUEBAS!) ---
@app.route('/init-db')
def init_db():
    with app.app_context():
        try:
            db.drop_all() # ¡CUIDADO! Esto borrará todas las tablas y datos existentes.
            print("Tablas existentes eliminadas (si las había).")
            db.create_all()
            print("Base de datos recreada.")

            # Insertar datos de prueba
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-001", estado="En ruta", cliente="KHS Mexico S.A. de C.V.", descripcion="Bomba de Agua", fecha_impresion=datetime(2024, 7, 10, 10, 0, 0)))
            db.session.add(Pedido(
                pedido_id_unico="PEDIDO-KHS-002",
                estado="Entregado",
                cliente="Cliente Ejemplo S.A.",
                descripcion="Componentes Electrónicos",
                fecha_impresion=datetime(2024, 7, 11, 14, 30, 0),
                nombre_cliente="Juan Perez",
                fecha_entrega=datetime(2024, 7, 11, 15, 0, 0),
                firma_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
                latitude="19.2833",
                longitude="-99.1333"
            ))
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-003", estado="En ruta", cliente="Proveedor Industrial", descripcion="Refacciones Varias", fecha_impresion=datetime(2024, 7, 12, 9, 15, 0)))
            db.session.commit()
            print("Pedidos de prueba añadidos a la base de datos.")
            flash("Base de datos inicializada y datos de prueba insertados con éxito.", "success")
        except Exception as e:
            print(f"ERROR: No se pudo inicializar la base de datos: {e}")
            traceback.print_exc() # Imprimir el traceback completo
            flash(f"Error al inicializar la base de datos: {e}. Revisa los logs de Render.", "error")
    return redirect(url_for('index'))


# --- Bloque de inicialización original (ahora solo para el primer arranque si no hay tablas) ---
with app.app_context():
    try:
        # Solo crea las tablas si no existen. La ruta /init-db las recrea forzadamente.
        db.create_all() 
        print("Base de datos creada/actualizada si no existía (desde el bloque principal).")

        # Este bloque solo se ejecutará si la tabla Pedido está completamente vacía
        # Si la base de datos ya tiene la tabla, pero sin datos, usa /init-db
        if Pedido.query.count() == 0:
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-001", estado="En ruta", cliente="KHS Mexico S.A. de C.V.", descripcion="Bomba de Agua", fecha_impresion=datetime(2024, 7, 10, 10, 0, 0)))
            db.session.add(Pedido(
                pedido_id_unico="PEDIDO-KHS-002",
                estado="Entregado",
                cliente="Cliente Ejemplo S.A.",
                descripcion="Componentes Electrónicos",
                fecha_impresion=datetime(2024, 7, 11, 14, 30, 0),
                nombre_cliente="Juan Perez",
                fecha_entrega=datetime(2024, 7, 11, 15, 0, 0),
                firma_base64="data:image/png;base64,iVBORw0KGgoAAAANSUgAEAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
                latitude="19.2833",
                longitude="-99.1333"
            ))
            db.session.add(Pedido(pedido_id_unico="PEDIDO-KHS-003", estado="En ruta", cliente="Proveedor Industrial", descripcion="Refacciones Varias", fecha_impresion=datetime(2024, 7, 12, 9, 15, 0)))
            db.session.commit()
            print("Pedidos de prueba añadidos a la base de datos (desde el bloque principal).")
    except Exception as e:
        print(f"ERROR: No se pudo conectar o inicializar la base de datos (desde el bloque principal): {e}")
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
        session.pop('_flashes', None)
        
        formatted_fecha_entrega = pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S") if pedido.fecha_entrega else 'N/A'
        flash(f'El pedido **{pedido_id_unico}** ya ha sido marcado como entregado el **{formatted_fecha_entrega}**.', 'info')
        
        # Preparar los datos para exito.html, asegurando que no sean None y sean strings
        nombre_cliente_display = pedido.nombre_cliente if pedido.nombre_cliente else 'N/A'
        firma_base64_display = pedido.firma_base64 if pedido.firma_base64 else ''
        # Aseguramos que latitude y longitude sean strings
        latitude_display = str(pedido.latitude) if pedido.latitude is not None else ''
        longitude_display = str(pedido.longitude) if pedido.longitude is not None else ''

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
            # Imprimir un error más detallado en la consola del servidor
            import traceback
            print(f"ERROR: Error al renderizar exito.html para pedido {pedido_id_unico}: {e}")
            traceback.print_exc() # Esto imprimirá el traceback completo
            flash(f'Error interno al mostrar los detalles del pedido: {e}. Revisa la consola del servidor para más detalles.', 'error')
            return redirect(url_for('error_page'))


    if request.method == 'POST':
        nombre_cliente = request.form['nombre_cliente']
        firma_base64 = request.form['firma_data']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not nombre_cliente or not firma_base64:
            flash('Por favor, ingrese su nombre y firme para confirmar la entrega.', 'error')
            return render_template('confirmar_entrega.html',
                                   pedido_id=pedido_id_unico,
                                   pedido=pedido)
        
        pedido.nombre_cliente = nombre_cliente
        pedido.firma_base64 = firma_base64
        pedido.fecha_entrega = datetime.now()
        pedido.estado = "Entregado"
        pedido.latitude = latitude
        pedido.longitude = longitude

        try:
            db.session.commit()
            session.pop('_flashes', None)
            flash('¡Entrega confirmada con éxito!', 'success')
            
            formatted_fecha_entrega = pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S") if pedido.fecha_entrega else 'N/A'
            return render_template('exito.html',
                                     pedido_id=pedido_id_unico,
                                     nombre_cliente=nombre_cliente,
                                     fecha_entrega=formatted_fecha_entrega,
                                     firma_base64=firma_base64,
                                     latitude=latitude,
                                     longitude=longitude)
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Error al guardar la confirmación del pedido {pedido_id_unico}: {e}")
            traceback.print_exc() # Imprimir el traceback completo
            flash(f'Error al guardar la confirmación: **{e}**. Revisa la consola del servidor.', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

    session.pop('_flashes', None)
    return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

@app.route('/error')
def error_page():
    return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
