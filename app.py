from flask import Flask, request, render_template, redirect, url_for, flash
from models import db, Pedido
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
# Para SQLite, es un archivo en tu proyecto.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://basedatos_envios_khs_5200:3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176@dpg-d1pgve49c44c738k7j4g-a.oregon-postgres.render.com/basedatos_envios_khs_5200')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '3QP4UN6ZUIDm2iw42GYVMMw3mhpTX176') # ¡CAMBIA ESTO EN PRODUCCIÓN!

db.init_app(app)

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

    # Opcional: Añadir algunos pedidos de prueba si la BD está vacía
    if Pedido.query.count() == 0:
        db.session.add(Pedido(pedido_id_unico="PEDIDO-XYZ-001", estado="En ruta"))
        db.session.add(Pedido(pedido_id_unico="PEDIDO-XYZ-002", estado="En ruta"))
        db.session.add(Pedido(pedido_id_unico="PEDIDO-XYZ-003", estado="En ruta"))
        db.session.commit()
        print("Pedidos de prueba añadidos a la base de datos.")


@app.route('/confirmar_entrega', methods=['GET', 'POST'])
def confirmar_entrega():
    pedido_id_unico = request.args.get('pedido_id')

    if not pedido_id_unico:
        flash('ID de pedido no proporcionado.', 'error')
        return redirect(url_for('error_page')) # Puedes crear una página de error genérica

    pedido = Pedido.query.filter_by(pedido_id_unico=pedido_id_unico).first()

    if not pedido:
        flash(f'Pedido con ID {pedido_id_unico} no encontrado.', 'error')
        return redirect(url_for('error_page'))

    if pedido.estado == "Entregado":
        flash(f'El pedido {pedido_id_unico} ya ha sido marcado como entregado el {pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S")}.', 'info')
        # Podrías redirigir a una página de "ya entregado" o mostrar solo la confirmación
        return render_template('exito.html', pedido_id=pedido_id_unico,
                               mensaje="Este pedido ya ha sido entregado.",
                               nombre_cliente=pedido.nombre_cliente,
                               fecha_entrega=pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S"),
                               firma_base64=pedido.firma_base64)


    if request.method == 'POST':
        nombre_cliente = request.form['nombre_cliente']
        firma_base64 = request.form['firma_data'] # Data de la firma desde el JS

        if not nombre_cliente or not firma_base64:
            flash('Por favor, ingrese su nombre y firme.', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

        pedido.nombre_cliente = nombre_cliente
        pedido.firma_base64 = firma_base64
        pedido.fecha_entrega = datetime.now()
        pedido.estado = "Entregado"

        try:
            db.session.commit()
            flash('¡Entrega confirmada con éxito!', 'success')
            return render_template('exito.html', pedido_id=pedido_id_unico,
                                   nombre_cliente=nombre_cliente,
                                   fecha_entrega=pedido.fecha_entrega.strftime("%Y-%m-%d %H:%M:%S"),
                                   firma_base64=firma_base64)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la confirmación: {e}', 'error')
            return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

    return render_template('confirmar_entrega.html', pedido_id=pedido_id_unico, pedido=pedido)

@app.route('/error')
def error_page():
    return render_template('error.html')

@app.route('/')
def index():
    return "Bienvenido al sistema de confirmación de entregas."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') # debug=True para desarrollo, ¡cambiar a False en producción!
                                      # host='0.0.0.0' para que sea accesible desde otras máquinas en la red local
