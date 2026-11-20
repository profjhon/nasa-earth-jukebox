import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "earth_jukebox.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de usuarios con control de roles (admin / explorador)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'explorador'
        )
    """)

    # Tabla principal del reto NASA: Pistas de sonorización de datos terrestres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pistas_tierra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            fenomeno TEXT NOT NULL,
            url_imagen TEXT NOT NULL,
            frecuencia_hz REAL NOT NULL,
            tipo_onda TEXT NOT NULL,
            intensidad INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    # Crear usuario administrador por defecto si no existe
    admin_existente = cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'").fetchone()
    if not admin_existente:
        cursor.execute(
            "INSERT INTO usuarios (nombre, username, password_hash, rol) VALUES (?, ?, ?, ?)",
            ("Administrador NASA EIC", "admin", generate_password_hash("admin123"), "admin")
        )
        admin_id = cursor.lastrowid

        # Cargar pistas de ejemplo basadas en datos del Earth Information Center (NASA)
        pistas_iniciales = [
            (
                "Anomalía Térmica Global (2026)",
                "Temperatura Superficial",
                "https://images-assets.nasa.gov/image/GSFC_20171208_Archive_e001435/GSFC_20171208_Archive_e001435~orig.jpg",
                440.0,
                "sine",
                75,
                "Sonorización de incremento térmico oceánico y terrestre registrado por satélites de observación terrestre.",
                admin_id
            ),
            (
                "Concentración Atmosférica de CO2",
                "Emisiones y Atmósfera",
                "https://images-assets.nasa.gov/image/PIA18033/PIA18033~orig.jpg",
                293.66,
                "triangle",
                60,
                "Frecuencia grave modulada que representa la densidad de dióxido de carbono en la troposfera.",
                admin_id
            ),
            (
                "Dinámica de Cobertura de Hielo Polar",
                "Criosfera y Nivel del Mar",
                "https://images-assets.nasa.gov/image/GSFC_20171208_Archive_e001016/GSFC_20171208_Archive_e001016~orig.jpg",
                587.33,
                "sawtooth",
                50,
                "Armónicos agudos que traducen la variación estacional del hielo marino ártico.",
                admin_id
            )
        ]
        cursor.executemany("""
            INSERT INTO pistas_tierra (titulo, fenomeno, url_imagen, frecuencia_hz, tipo_onda, intensidad, descripcion, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, pistas_iniciales)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos earth_jukebox.db inicializada correctamente.")