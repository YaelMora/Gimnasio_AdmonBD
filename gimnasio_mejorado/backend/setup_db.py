# backend/setup_db.py
import sqlite3
import os
from db_config import DATABASE_FILE, INSTANCE_FOLDER
import bcrypt
import logging # Añadido para logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s [%(funcName)s]')


def hash_password_for_setup(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def initialize_database():
    """
    Crea las tablas en la base de datos SQLite si no existen,
    leyendo el esquema desde schema.sql e inserta datos de prueba.
    La base de datos se creará en la carpeta 'instance'.
    """
    if not os.path.exists(INSTANCE_FOLDER):
        try:
            os.makedirs(INSTANCE_FOLDER)
            logging.info(f"Directorio 'instance' creado por setup_db.py en: {INSTANCE_FOLDER}")
        except OSError as e:
            logging.error(f"Error al crear el directorio 'instance' desde setup_db.py: {e}")
            return

    conn = None
    try:
        logging.info(f"Intentando conectar/crear base de datos en: {DATABASE_FILE}")
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if not os.path.exists(schema_path):
            logging.error(f"Error: No se encontró el archivo schema.sql en {schema_path}")
            return

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        conn.commit()
        logging.info(f"Base de datos '{DATABASE_FILE}' inicializada/verificada exitosamente.")

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        logging.info("Claves foráneas habilitadas.")

        logging.info("Insertando datos de prueba (si no existen)...")

        # Gerentes de Prueba
        gerentes_prueba = [
            ('Ana', 'Torres', '5512345670', 'ana.torres@example.com', 'TOTL850101ABC', hash_password_for_setup('password123')),
            ('Carlos', 'Lopez', '5598765430', 'carlos.lopez@example.com', 'LOPC900202XYZ', hash_password_for_setup('securepass'))
        ]
        
        for gerente_data in gerentes_prueba:
            cursor.execute("SELECT id FROM gerentes WHERE correo = ?", (gerente_data[3],))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO gerentes (nombre, apellido, telefono, correo, rfc, contrasena_hash) VALUES (?, ?, ?, ?, ?, ?)", gerente_data)
                logging.info(f"Gerente de prueba insertado: {gerente_data[3]}")
        
        conn.commit()

        # Miembros de Prueba
        miembros_prueba = [
            ('Juan', 'Perez', '5511223344', 'juan.perez@example.com', hash_password_for_setup('juanito123'), '1 Mes', '2024-05-01', '2024-05-31', 'vencida'),
            ('Maria', 'Garcia', '5555667788', 'maria.garcia@example.com', hash_password_for_setup('maria456'), '3 Meses', '2024-06-01', '2024-08-31', 'activa'),
            ('Luis', 'Hernandez', '5543219876', 'luis.hernandez@example.com', hash_password_for_setup('luis789'), '6 Meses', '2024-03-15', '2024-09-15', 'activa'),
            ('Laura', 'Martinez', '5510203040', 'laura.martinez@example.com', hash_password_for_setup('laurapass'), '1 Mes', '2024-07-01', '2024-07-31', 'activa')
        ]

        for miembro_data in miembros_prueba:
            cursor.execute("SELECT id FROM miembros WHERE correo = ?", (miembro_data[3],))
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO miembros (nombre, apellido, telefono, correo, contrasena_hash, 
                                          tipo_membresia, fecha_inicio_membresia, 
                                          fecha_vencimiento_membresia, estado_membresia) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, miembro_data)
                logging.info(f"Miembro de prueba insertado: {miembro_data[3]}")

        conn.commit()
        logging.info("Datos de prueba insertados (si no existían previamente).")

    except sqlite3.Error as e:
        logging.error(f"Error al inicializar la base de datos o insertar datos de prueba: {e}")
    except Exception as ex:
        logging.error(f"Un error inesperado ocurrió: {ex}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    initialize_database()
