from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from .db import get_db
from datetime import datetime
import os

bp = Blueprint('main', __name__)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
CATEGORIAS_DISPONIBLES = [
    'Panes',
    'Pasteles',
    'Bollería',
    'Galletas',
    'Especiales',
    'Sin Gluten',
    'Integrales'
]


def extension_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login del administrador
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM administradores WHERE usuario = %s AND password = %s", (usuario, password))
        admin = cursor.fetchone()

        if admin:
            session['admin_id'] = admin['id']
            session['usuario'] = admin['usuario']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

# Dashboard de productos
@bp.route('/admin/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    # Obtener las categorías existentes de la tabla categorias
    cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    categorias = cursor.fetchall()

    return render_template('dashboard.html', productos=productos, categorias=categorias, year=datetime.now().year)



# Agregar producto
@bp.route('/admin/productos/agregar', methods=['POST'])
def agregar_producto():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    nombre = request.form['nombre']
    precio = request.form['precio']
    categoria = request.form['categoria']
    descripcion = request.form['descripcion']
    imagen = request.files['imagen']
    ruta_imagen = ''

    if imagen and imagen.filename != '':
        if not extension_permitida(imagen.filename):
            flash('Formato de imagen no permitido.')
            return redirect(url_for('main.dashboard'))
        filename = secure_filename(imagen.filename)
        carpeta = current_app.config['UPLOAD_FOLDER']
        os.makedirs(carpeta, exist_ok=True)
        imagen.save(os.path.join(carpeta, filename))
        ruta_imagen = f'uploads/{filename}'

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO productos (nombre, descripcion, precio, imagen, categoria)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, descripcion, precio, ruta_imagen, categoria))
    db.commit()
    return redirect(url_for('main.dashboard'))

# Editar producto
@bp.route('/admin/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        categoria = request.form['categoria']
        descripcion = request.form['descripcion']
        imagen_actual = request.form.get('imagen_actual')
        imagen_nueva = request.files.get('imagen')
        imagen_path = imagen_actual

        if imagen_nueva and imagen_nueva.filename != '':
            if not extension_permitida(imagen_nueva.filename):
                flash('Formato de imagen no permitido.')
                return redirect(url_for('main.editar_producto', id=id))
            filename = secure_filename(imagen_nueva.filename)
            carpeta = current_app.config['UPLOAD_FOLDER']
            os.makedirs(carpeta, exist_ok=True)
            imagen_nueva.save(os.path.join(carpeta, filename))
            imagen_path = f'uploads/{filename}'

        cursor.execute("""
            UPDATE productos SET nombre=%s, descripcion=%s, precio=%s, imagen=%s, categoria=%s
            WHERE id = %s
        """, (nombre, descripcion, precio, imagen_path, categoria, id))
        db.commit()
        return redirect(url_for('main.dashboard'))

    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cursor.fetchone()
    return render_template('editar_producto.html', producto=producto)

# Eliminar producto
@bp.route('/admin/productos/eliminar/<int:id>')
def eliminar_producto(id):
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for('main.dashboard'))

# ---------------------
# FUNCIONALIDAD DE ANUNCIOS
# ---------------------

# Vista de administración de anuncios
@bp.route('/admin/anuncios')
def admin_anuncios():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM anuncios ORDER BY fecha_publicacion DESC")
    anuncios = cursor.fetchall()

    return render_template('anuncios.html', anuncios=anuncios)



# Agregar anuncio
@bp.route('/admin/anuncios/agregar', methods=['POST'])
def agregar_anuncio():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')

    if not titulo or not contenido:
        flash("Todos los campos son obligatorios.")
        return redirect(url_for('main.admin_anuncios')) 

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO anuncios (titulo, contenido)
        VALUES (%s, %s)
    """, (titulo, contenido))
    db.commit()

    return redirect(url_for('main.admin_anuncios')) 



# Eliminar anuncio
@bp.route('/admin/anuncios/eliminar/<int:id>')
def eliminar_anuncio(id):
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM anuncios WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for('main.admin_anuncios'))



@bp.route('/')
def home():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Obtener anuncios
    cursor.execute("SELECT * FROM anuncios ORDER BY creado DESC LIMIT 3")
    anuncios = cursor.fetchall()

    # Obtener productos (puedes limitar si quieres solo los más recientes)
    cursor.execute("SELECT * FROM productos ORDER BY id DESC LIMIT 4")
    productos = cursor.fetchall()

    return render_template('index.html', anuncios=anuncios, productos=productos)

@bp.route('/admin/categorias/agregar', methods=['POST'])
def agregar_categoria():
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    nombre = request.form.get('nombre')

    if not nombre:
        flash("El nombre de la categoría es obligatorio.")
        return redirect(url_for('main.dashboard'))

    db = get_db()
    cursor = db.cursor()

    # Verifica si ya existe (opcional pero recomendado)
    cursor.execute("SELECT COUNT(*) FROM categorias WHERE nombre = %s", (nombre,))
    if cursor.fetchone()[0] > 0:
        flash("La categoría ya existe.")
        return redirect(url_for('main.dashboard'))

    cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nombre,))
    db.commit()
    flash("Categoría agregada correctamente.")
    return redirect(url_for('main.dashboard'))


@bp.route('/admin/categorias/eliminar/<int:id>')
def eliminar_categoria(id):
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    db = get_db()
    cursor = db.cursor()

    # Verificamos si hay productos asociados (opcional pero recomendable)
    cursor.execute("SELECT COUNT(*) FROM productos WHERE categoria_id = %s", (id,))
    if cursor.fetchone()[0] > 0:
        flash("No puedes eliminar esta categoría porque está asignada a productos.")
        return redirect(url_for('main.dashboard'))

    cursor.execute("DELETE FROM categorias WHERE id = %s", (id,))
    db.commit()
    flash("Categoría eliminada correctamente.")
    return redirect(url_for('main.dashboard'))


@bp.route('/admin/categorias/editar/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        nuevo_nombre = request.form.get('nombre')
        if not nuevo_nombre:
            flash('El nombre no puede estar vacío.')
            return redirect(url_for('main.editar_categoria', id=id))

        cursor.execute("UPDATE categorias SET nombre = %s WHERE id = %s", (nuevo_nombre, id))
        db.commit()
        flash("Categoría actualizada correctamente.")
        return redirect(url_for('main.dashboard'))

    # GET: obtener categoría actual
    cursor.execute("SELECT * FROM categorias WHERE id = %s", (id,))
    categoria = cursor.fetchone()

    if not categoria:
        flash("Categoría no encontrada.")
        return redirect(url_for('main.dashboard'))

    return render_template('editar_categoria.html', categoria=categoria)


@bp.route('/productos')
def productos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    return render_template('productos.html', productos=productos)

@bp.route('/sobre-nosotros')
def sobre_nosotros():
    return render_template('sobre-nosotros.html')

@bp.route('/contacto')
def contacto():
    return render_template('contacto.html')




