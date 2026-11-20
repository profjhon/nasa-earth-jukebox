import os
import pytest
import database
from app import app

@pytest.fixture
def client(tmp_path):
    # Usar una base de datos temporal aislada para no tocar tus datos reales
    test_db = tmp_path / "test_jukebox.db"
    database.DB_NAME = str(test_db)
    database.init_db()

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client

def test_01_redireccion_sin_sesion(client):
    """Verifica que un usuario sin sesión sea redirigido al login"""
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

def test_02_registro_e_inicio_sesion(client):
    """Verifica el registro de un usuario explorador y su posterior login"""
    resp_reg = client.post("/register", data={
        "nombre": "Investigador Prueba",
        "username": "explorador1",
        "password": "claveSegura123"
    }, follow_redirects=True)
    assert resp_reg.status_code == 200
    assert b"Registro exitoso" in resp_reg.data

    resp_login = client.post("/login", data={
        "username": "explorador1",
        "password": "claveSegura123"
    }, follow_redirects=True)
    assert resp_login.status_code == 200
    assert b"Investigador Prueba" in resp_login.data

def test_03_crud_pistas_terrestres(client):
    """Verifica Crear, Leer, Actualizar y Eliminar (CRUD) una pista en SQLite"""
    # Iniciar sesión como admin por defecto
    client.post("/login", data={"username": "admin", "password": "admin123"})

    # 1. CREAR (Create)
    resp_create = client.post("/pista/crear", data={
        "titulo": "Tormenta Solar Test",
        "fenomeno": "Actividad Geomagnética",
        "url_imagen": "https://images-assets.nasa.gov/image/PIA18033/PIA18033~orig.jpg",
        "frecuencia_hz": "528.0",
        "tipo_onda": "sine",
        "intensidad": "80",
        "descripcion": "Prueba automatizada de creación."
    }, follow_redirects=True)
    assert b"Tormenta Solar Test" in resp_create.data

    # Obtener ID de la pista recién creada
    conn = database.get_db_connection()
    pista = conn.execute("SELECT id FROM pistas_tierra WHERE titulo = 'Tormenta Solar Test'").fetchone()
    conn.close()
    assert pista is not None
    pista_id = pista["id"]

    # 2. ACTUALIZAR (Update)
    resp_edit = client.post(f"/pista/editar/{pista_id}", data={
        "titulo": "Tormenta Solar Actualizada",
        "fenomeno": "Actividad Geomagnética",
        "url_imagen": "https://images-assets.nasa.gov/image/PIA18033/PIA18033~orig.jpg",
        "frecuencia_hz": "639.0",
        "tipo_onda": "triangle",
        "intensidad": "85",
        "descripcion": "Descripción editada por pytest."
    }, follow_redirects=True)
    assert b"Tormenta Solar Actualizada" in resp_edit.data

    # 3. ELIMINAR (Delete)
    resp_del = client.post(f"/pista/eliminar/{pista_id}", follow_redirects=True)
    assert b"Pista eliminada del registro" in resp_del.data

def test_04_control_acceso_roles(client):
    """Verifica que un usuario explorador NO pueda entrar al panel de admin"""
    client.post("/register", data={
        "nombre": "Usuario Normal",
        "username": "user_normal",
        "password": "123"
    })
    client.post("/login", data={"username": "user_normal", "password": "123"})

    resp = client.get("/admin/usuarios", follow_redirects=True)
    assert b"Acceso denegado" in resp.data