import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nasa_space_apps_2026_jukebox_key")

# Inicializar la base de datos al arrancar
init_db()

# --- DECORADORES DE SEGURIDAD Y ROLES ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión para acceder a la Jukebox.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rol") != "admin":
            flash("Acceso denegado: Se requieren permisos de Administrador.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE AUTENTICACIÓN ---
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["nombre"] = user["nombre"]
            session["username"] = user["username"]
            session["rol"] = user["rol"]
            flash(f"Bienvenido a Earth Jukebox, {user['nombre']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]

        if not nombre or not username or not password:
            flash("Todos los campos son obligatorios.", "warning")
            return redirect(url_for("register"))

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO usuarios (nombre, username, password_hash, rol) VALUES (?, ?, ?, ?)",
                (nombre, username, generate_password_hash(password), "explorador")
            )
            conn.commit()
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except Exception:
            flash("El nombre de usuario ya está en uso. Elige otro.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))

# --- RUTAS PRINCIPALES Y CRUD DE PISTAS TERRESTRES ---
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    pistas = conn.execute("""
        SELECT p.*, u.nombre AS autor 
        FROM pistas_tierra p 
        JOIN usuarios u ON p.usuario_id = u.id 
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()
    return render_template("dashboard.html", pistas=pistas)

@app.route("/pista/crear", methods=["POST"])
@login_required
def crear_pista():
    titulo = request.form["titulo"].strip()
    fenomeno = request.form["fenomeno"].strip()
    url_imagen = request.form["url_imagen"].strip()
    frecuencia_hz = float(request.form["frecuencia_hz"])
    tipo_onda = request.form["tipo_onda"]
    intensidad = int(request.form["intensidad"])
    descripcion = request.form["descripcion"].strip()

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO pistas_tierra (titulo, fenomeno, url_imagen, frecuencia_hz, tipo_onda, intensidad, descripcion, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, fenomeno, url_imagen, frecuencia_hz, tipo_onda, intensidad, descripcion, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Nueva pista de sonorización creada exitosamente.", "success")
    return redirect(url_for("dashboard"))

@app.route("/pista/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_pista(id):
    conn = get_db_connection()
    pista = conn.execute("SELECT * FROM pistas_tierra WHERE id = ?", (id,)).fetchone()

    if not pista:
        conn.close()
        flash("La pista solicitada no existe.", "danger")
        return redirect(url_for("dashboard"))

    # Control de permisos: solo el dueño de la pista o un admin puede editarla
    if pista["usuario_id"] != session["user_id"] and session.get("rol") != "admin":
        conn.close()
        flash("No tienes permisos para editar esta pista.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        fenomeno = request.form["fenomeno"].strip()
        url_imagen = request.form["url_imagen"].strip()
        frecuencia_hz = float(request.form["frecuencia_hz"])
        tipo_onda = request.form["tipo_onda"]
        intensidad = int(request.form["intensidad"])
        descripcion = request.form["descripcion"].strip()

        conn.execute("""
            UPDATE pistas_tierra 
            SET titulo = ?, fenomeno = ?, url_imagen = ?, frecuencia_hz = ?, tipo_onda = ?, intensidad = ?, descripcion = ?
            WHERE id = ?
        """, (titulo, fenomeno, url_imagen, frecuencia_hz, tipo_onda, intensidad, descripcion, id))
        conn.commit()
        conn.close()

        flash("Pista actualizada correctamente.", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("editar.html", pista=pista)

@app.route("/pista/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_pista(id):
    conn = get_db_connection()
    pista = conn.execute("SELECT * FROM pistas_tierra WHERE id = ?", (id,)).fetchone()

    if not pista:
        conn.close()
        flash("La pista no existe.", "danger")
        return redirect(url_for("dashboard"))

    # Control de permisos: solo el dueño o un admin puede eliminarla
    if pista["usuario_id"] != session["user_id"] and session.get("rol") != "admin":
        conn.close()
        flash("No tienes permisos para eliminar esta pista.", "danger")
        return redirect(url_for("dashboard"))

    conn.execute("DELETE FROM pistas_tierra WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Pista eliminada del registro.", "info")
    return redirect(url_for("dashboard"))

# --- MÓDULO EXCLUSIVO DE ADMINISTRADOR (GESTIÓN DE ROLES) ---
@app.route("/admin/usuarios")
@login_required
@admin_required
def admin_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute("SELECT id, nombre, username, rol FROM usuarios ORDER BY id ASC").fetchall()
    conn.close()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@app.route("/admin/usuarios/rol/<int:id>", methods=["POST"])
@login_required
@admin_required
def cambiar_rol(id):
    nuevo_rol = request.form["rol"]
    if nuevo_rol in ["admin", "explorador"]:
        conn = get_db_connection()
        conn.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (nuevo_rol, id))
        conn.commit()
        conn.close()
        flash("Rol de usuario actualizado.", "success")
    return redirect(url_for("admin_usuarios"))

if __name__ == "__main__":
    app.run(debug=True)