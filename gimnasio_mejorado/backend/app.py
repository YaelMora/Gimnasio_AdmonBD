# backend/app.py
import os
import sqlite3
import bcrypt
from flask import Flask, request, jsonify, send_from_directory, send_file 
from flask_cors import CORS 
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
import logging

# QR Code
import qrcode
# import io # Se moverá a la función que lo usa (descargar_reporte_excel_api)
# import openpyxl # Se moverá a la función que lo usa (descargar_reporte_excel_api)

# Importar configuración
from db_config import (
    DATABASE_FILE,
    UPLOAD_FOLDER_MEMBER_IMAGES,
    ALLOWED_EXTENSIONS,
    UPLOAD_URL_PATH_MEMBER_IMAGES,
    UPLOAD_FOLDER_QRS,
    UPLOAD_URL_PATH_QRS
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s [%(funcName)s]')

app = Flask(__name__, static_folder='static') 

# Configurar CORS para exponer el header Content-Disposition
CORS(app, expose_headers=['Content-Disposition'])

# --- Conexión a la Base de Datos SQLite ---
def get_db_connection():
    """Establece conexión con la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row 
        conn.execute("PRAGMA foreign_keys = ON;") 
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con SQLite: {e}")
        raise 

# --- Funciones Auxiliares ---
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    if not password or not hashed_password: 
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rutas API ---

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hola desde el backend del Gimnasio con SQLite!"})

# --- GERENTES (Endpoints de Gerentes) ---
@app.route('/api/gerentes/validar', methods=['POST'])
def validar_gerente_api():
    data = request.get_json()
    id_gerente_input = data.get('idGerente') 
    contrasena = data.get('contrasena')
    if not id_gerente_input or not contrasena:
        return jsonify({"message": "ID/Correo de Gerente y contraseña son requeridos"}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT id, contrasena_hash FROM gerentes WHERE correo = ?"
        params = (id_gerente_input,)
        if str(id_gerente_input).isdigit():
            query = "SELECT id, contrasena_hash FROM gerentes WHERE id = ? OR correo = ?"
            params = (int(id_gerente_input), id_gerente_input)
        cursor.execute(query, params)
        gerente = cursor.fetchone()
        if gerente and check_password(contrasena, gerente['contrasena_hash']):
            return jsonify({"message": "Gerente validado exitosamente", "idGerente": gerente['id']}), 200
        else:
            return jsonify({"message": "ID/Correo de Gerente o contraseña incorrectos"}), 401
    except sqlite3.Error as e:
        logging.error(f"Error DB validando gerente: {e}")
        return jsonify({"message": "Error interno del servidor al validar gerente"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/gerentes', methods=['POST'])
def registrar_gerente_api():
    data = request.get_json()
    required_fields = ['nombreGerente', 'apellidoGerente', 'correoGerente', 'contrasena', 'rfcGerente']
    if not all(k in data and data[k] for k in required_fields):
        return jsonify({"message": "Faltan campos requeridos o están vacíos"}), 400
    hashed_pass = hash_password(data['contrasena'])
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO gerentes (nombre, apellido, telefono, correo, rfc, contrasena_hash) VALUES (?, ?, ?, ?, ?, ?)"
        val = (data['nombreGerente'], data['apellidoGerente'], data.get('telefonoGerente'), data['correoGerente'], data['rfcGerente'], hashed_pass)
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"message": "Gerente registrado exitosamente", "id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        if 'correo' in str(e).lower(): return jsonify({"message": f"Error: El correo '{data['correoGerente']}' ya existe."}), 409
        elif 'rfc' in str(e).lower(): return jsonify({"message": f"Error: El RFC '{data['rfcGerente']}' ya existe."}), 409
        logging.error(f"Error de integridad DB registrando gerente: {e}")
        return jsonify({"message": "Error de unicidad al registrar gerente (correo o RFC ya existen)"}), 409
    except sqlite3.Error as e:
        logging.error(f"Error DB registrando gerente: {e}")
        return jsonify({"message": "Error al registrar gerente"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/gerentes', methods=['GET'])
def obtener_gerentes_api():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, apellido, telefono, correo, rfc, strftime('%Y-%m-%d %H:%M:%S', fecha_registro) as fecha_registro FROM gerentes")
        gerentes = cursor.fetchall()
        return jsonify([dict(row) for row in gerentes]), 200
    except sqlite3.Error as e:
        logging.error(f"Error DB obteniendo gerentes: {e}")
        return jsonify({"message": "Error al obtener gerentes"}), 500
    finally:
        if conn: conn.close()
            
@app.route('/api/gerentes/<int:id_gerente>', methods=['PUT'])
def actualizar_gerente_api(id_gerente):
    data = request.get_json()
    if not data: return jsonify({"message": "No se proporcionaron datos para actualizar"}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        update_fields = []
        update_values = []
        allowed_to_update_map = {'nombre': 'nombreGerente', 'apellido': 'apellidoGerente', 'telefono': 'telefonoGerente', 'correo': 'correoGerente', 'rfc': 'rfcGerente'}
        for db_col, json_key in allowed_to_update_map.items():
            if json_key in data: 
                update_fields.append(f"{db_col} = ?")
                update_values.append(data[json_key])
        
        if not update_fields: return jsonify({"message": "No hay campos válidos para actualizar"}), 400
        update_values.append(id_gerente) 
        sql = f"UPDATE gerentes SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(sql, tuple(update_values))
        conn.commit()
        if cursor.rowcount == 0: return jsonify({"message": "Gerente no encontrado o sin cambios"}), 404
        return jsonify({"message": "Gerente actualizado exitosamente"}), 200
    except sqlite3.IntegrityError as e: return jsonify({"message": f"Error de unicidad: {str(e)}"}), 409
    except sqlite3.Error as e:
        logging.error(f"Error DB actualizando gerente: {e}")
        return jsonify({"message": "Error al actualizar gerente"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/gerentes/<int:id_gerente>', methods=['DELETE'])
def eliminar_gerente_api(id_gerente):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gerentes WHERE id = ?", (id_gerente,))
        conn.commit()
        if cursor.rowcount == 0: return jsonify({"message": "Gerente no encontrado"}), 404
        return jsonify({"message": "Gerente eliminado exitosamente"}), 200
    except sqlite3.Error as e:
        logging.error(f"Error DB eliminando gerente: {e}")
        return jsonify({"message": "Error al eliminar gerente"}), 500
    finally:
        if conn: conn.close()

# --- MIEMBROS (Endpoints de Miembros) ---
@app.route('/api/miembros', methods=['POST'])
def registrar_miembro_api():
    data = request.get_json()
    required_fields = ['nombre', 'apellido', 'membresia', 'contrasena', 'gerenteId', 'contrasenaGerente']
    if not all(k in data and (data[k] or k in ['telefono', 'correo']) for k in required_fields):
        return jsonify({"message": "Faltan campos requeridos para registrar miembro o están vacíos"}), 400
    if len(data['contrasena']) < 6:
        return jsonify({"message": "La contraseña del miembro debe tener al menos 6 caracteres"}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query_gerente = "SELECT id, contrasena_hash FROM gerentes WHERE id = ? OR correo = ?"
        params_gerente = (data['gerenteId'], data['gerenteId'])
        if str(data['gerenteId']).isdigit():
             params_gerente = (int(data['gerenteId']), data['gerenteId'])
        else: 
            query_gerente = "SELECT id, contrasena_hash FROM gerentes WHERE correo = ?"
            params_gerente = (data['gerenteId'],)
        cursor.execute(query_gerente, params_gerente)
        gerente = cursor.fetchone()
        if not (gerente and check_password(data['contrasenaGerente'], gerente['contrasena_hash'])):
            return jsonify({"message": "Credenciales de gerente inválidas"}), 401
        hashed_member_pass = hash_password(data['contrasena'])
        fecha_inicio_membresia = datetime.now(timezone.utc) 
        tipo_membresia = data['membresia']
        dias_membresia = 0
        if tipo_membresia == "1 Mes": dias_membresia = 30
        elif tipo_membresia == "3 Meses": dias_membresia = 90
        elif tipo_membresia == "6 Meses": dias_membresia = 180
        if dias_membresia == 0: return jsonify({"message": "Tipo de membresía inválido"}), 400
        fecha_vencimiento_membresia = fecha_inicio_membresia + timedelta(days=dias_membresia)
        sql_miembro = """
            INSERT INTO miembros (nombre, apellido, telefono, correo, contrasena_hash, tipo_membresia, 
                                  fecha_inicio_membresia, fecha_vencimiento_membresia, estado_membresia) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        val_miembro = (
            data['nombre'], data['apellido'], data.get('telefono'), data.get('correo'),
            hashed_member_pass, tipo_membresia, fecha_inicio_membresia.strftime('%Y-%m-%d'), 
            fecha_vencimiento_membresia.strftime('%Y-%m-%d'), 'activa'
        )
        cursor.execute(sql_miembro, val_miembro)
        conn.commit()
        miembro_id = cursor.lastrowid
        return jsonify({"message": "Miembro registrado exitosamente", "id": miembro_id, "nombre": data['nombre']}), 201
    except sqlite3.IntegrityError as e:
        if 'miembros.correo' in str(e).lower():
             return jsonify({"message": f"Error: El correo '{data.get('correo')}' ya existe para otro miembro."}), 409
        logging.error(f"Error de integridad DB registrando miembro: {e}")
        return jsonify({"message": "Error de unicidad al registrar miembro"}), 409
    except sqlite3.Error as e:
        logging.error(f"Error DB registrando miembro: {e}")
        return jsonify({"message": "Error al registrar miembro"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/miembros/<int:id_miembro>/validar_acceso', methods=['POST'])
def validar_acceso_miembro_api(id_miembro):
    data = request.get_json()
    contrasena = data.get('contrasena')
    if not contrasena: return jsonify({"message": "Contraseña es requerida"}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, apellido, contrasena_hash, estado_membresia FROM miembros WHERE id = ?", (id_miembro,))
        miembro = cursor.fetchone()
        if miembro and check_password(contrasena, miembro['contrasena_hash']):
            if miembro['estado_membresia'] != 'activa':
                return jsonify({"message": f"Acceso denegado: La membresía de {miembro['nombre']} {miembro['apellido']} no está activa.", "accesoPermitido": False}), 403
            return jsonify({"message": "Acceso validado exitosamente.", "accesoPermitido": True, "miembroId": miembro['id'], "nombreCompleto": f"{miembro['nombre']} {miembro['apellido']}"}), 200
        else:
            return jsonify({"message": "ID de Miembro o contraseña incorrectos", "accesoPermitido": False}), 401
    except sqlite3.Error as e:
        logging.error(f"Error DB validando acceso de miembro: {e}")
        return jsonify({"message": "Error interno del servidor al validar acceso"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/miembros', methods=['GET'])
def obtener_miembros_api():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE miembros SET estado_membresia = 'vencida' WHERE fecha_vencimiento_membresia < date('now', 'localtime') AND estado_membresia = 'activa'")
        conn.commit()
        cursor.execute("""
            SELECT id, nombre, apellido, telefono, correo, 
                   strftime('%Y-%m-%d', fecha_inicio_membresia) as fechaInicio, 
                   strftime('%Y-%m-%d', fecha_vencimiento_membresia) as fechaVencimiento, 
                   estado_membresia, tipo_membresia 
            FROM miembros ORDER BY id DESC
        """)
        miembros = cursor.fetchall()
        return jsonify([dict(row) for row in miembros]), 200
    except sqlite3.Error as e:
        logging.error(f"Error DB obteniendo miembros: {e}")
        return jsonify({"message": "Error al obtener miembros"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/miembros/<int:id_miembro>', methods=['PUT'])
def actualizar_miembro_api(id_miembro):
    data = request.get_json()
    if not data: return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400
    
    logging.info(f"Actualizando miembro ID {id_miembro} con datos: {data}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        update_fields = []
        update_values = []
        
        # Campos básicos del miembro
        allowed_to_update_map = {'nombre': 'nombre', 'apellido': 'apellido', 'telefono': 'telefono', 'correo': 'correo'}
        for db_col, json_key in allowed_to_update_map.items():
            if json_key in data and data[json_key] is not None: # Solo actualizar si el campo existe en el JSON y no es null
                update_fields.append(f"{db_col} = ?")
                update_values.append(data[json_key])
        
        # Actualización de contraseña
        if 'contrasena' in data and data['contrasena']: # Si se provee una nueva contraseña
            if len(data['contrasena']) < 6: 
                return jsonify({"message": "La nueva contraseña debe tener al menos 6 caracteres."}), 400
            hashed_pass = hash_password(data['contrasena'])
            update_fields.append("contrasena_hash = ?")
            update_values.append(hashed_pass)

        # Lógica para renovar/cambiar membresía
        if 'duracionMembresia' in data and data['duracionMembresia']: 
            nueva_tipo_membresia = data['duracionMembresia']
            fecha_inicio_nueva_membresia = datetime.now(timezone.utc) 
            dias_nueva_membresia = 0
            if nueva_tipo_membresia == "1 Mes": dias_nueva_membresia = 30
            elif nueva_tipo_membresia == "3 Meses": dias_nueva_membresia = 90
            elif nueva_tipo_membresia == "6 Meses": dias_nueva_membresia = 180

            if dias_nueva_membresia > 0:
                fecha_vencimiento_nueva = fecha_inicio_nueva_membresia + timedelta(days=dias_nueva_membresia)
                update_fields.extend(["tipo_membresia = ?", "fecha_inicio_membresia = ?", "fecha_vencimiento_membresia = ?", "estado_membresia = ?"])
                update_values.extend([
                    nueva_tipo_membresia, 
                    fecha_inicio_nueva_membresia.strftime('%Y-%m-%d'), 
                    fecha_vencimiento_nueva.strftime('%Y-%m-%d'), 
                    'activa'
                ])
            else: 
                # Si se envía duracionMembresia pero no es una opción válida
                logging.warning(f"Intento de actualizar membresía con duración inválida: {nueva_tipo_membresia}")
                return jsonify({"message": "Duración de membresía para renovación/cambio es inválida."}), 400
        
        # Actualización manual de fecha de vencimiento (si no se renueva por duración)
        elif 'fechaVencimiento' in data and data['fechaVencimiento']: 
            try:
                # Validar el formato de la fecha
                fv_obj = datetime.strptime(data['fechaVencimiento'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                update_fields.append("fecha_vencimiento_membresia = ?")
                update_values.append(data['fechaVencimiento'])
                # Actualizar estado basado en la nueva fecha de vencimiento
                estado_actualizado = 'activa' if fv_obj.date() >= datetime.now(timezone.utc).date() else 'vencida'
                update_fields.append("estado_membresia = ?")
                update_values.append(estado_actualizado)
            except ValueError:
                 logging.warning(f"Formato de fechaVencimiento inválido: {data['fechaVencimiento']}")
                 return jsonify({"message": "Formato de fecha de vencimiento inválido. Usar YYYY-MM-DD."}), 400

        if not update_fields: 
            logging.info(f"No hay campos válidos para actualizar para miembro ID {id_miembro}")
            return jsonify({"message": "No hay campos válidos para actualizar o no se proporcionaron datos nuevos."}), 400
        
        update_values.append(id_miembro) # Para la cláusula WHERE id = ?
        sql = f"UPDATE miembros SET {', '.join(update_fields)} WHERE id = ?"
        
        logging.info(f"Ejecutando SQL de actualización para miembro ID {id_miembro}: {sql} con valores: {update_values}")
        cursor.execute(sql, tuple(update_values))
        conn.commit()

        if cursor.rowcount == 0: 
            logging.warning(f"Miembro ID {id_miembro} no encontrado o ningún dato fue diferente para actualizar.")
            return jsonify({"message": "Miembro no encontrado o ningún dato fue diferente para actualizar."}), 404
            
        logging.info(f"Miembro ID {id_miembro} actualizado exitosamente.")
        return jsonify({"message": "Miembro actualizado exitosamente"}), 200
    except sqlite3.IntegrityError as e:
        if 'miembros.correo' in str(e).lower(): # Chequeo de unicidad de correo
             logging.error(f"Error de unicidad de correo para miembro ID {id_miembro}: {e}")
             return jsonify({"message": f"Error: El correo '{data.get('correo')}' ya existe para otro miembro."}), 409
        logging.error(f"Error de integridad DB actualizando miembro ID {id_miembro}: {e}")
        return jsonify({"message": "Error de unicidad al actualizar miembro."}), 409
    except sqlite3.Error as e:
        logging.error(f"Error DB actualizando miembro ID {id_miembro}: {e}")
        return jsonify({"message": "Error al actualizar miembro."}), 500
    except Exception as e_general:
        logging.error(f"Error general actualizando miembro ID {id_miembro}: {e_general}", exc_info=True)
        return jsonify({"message": f"Error inesperado en el servidor: {str(e_general)}"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/miembros/<int:id_miembro>', methods=['DELETE'])
def eliminar_miembro_api(id_miembro):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ruta_imagen FROM imagenes_miembros WHERE miembro_id = ?", (id_miembro,))
        imagenes_a_borrar = cursor.fetchall()
        for img_row in imagenes_a_borrar:
            if img_row['ruta_imagen']:
                ruta_completa_img = os.path.join(UPLOAD_FOLDER_MEMBER_IMAGES, img_row['ruta_imagen'])
                if os.path.exists(ruta_completa_img):
                    try:
                        os.remove(ruta_completa_img)
                        logging.info(f"Imagen eliminada del servidor: {ruta_completa_img}")
                    except OSError as e_os:
                        logging.error(f"Error eliminando archivo de imagen {ruta_completa_img}: {e_os}")
        cursor.execute("DELETE FROM miembros WHERE id = ?", (id_miembro,))
        conn.commit()
        if cursor.rowcount == 0: return jsonify({"message": "Miembro no encontrado"}), 404
        return jsonify({"message": "Miembro eliminado exitosamente"}), 200
    except sqlite3.Error as e:
        logging.error(f"Error DB eliminando miembro: {e}")
        return jsonify({"message": "Error al eliminar miembro"}), 500
    finally:
        if conn: conn.close()

# --- Endpoint para Generar y Guardar QR ---
@app.route('/api/miembros/<int:id_miembro>/generar_qr', methods=['POST'])
def generar_guardar_qr_miembro_api(id_miembro):
    logging.info(f"Solicitud para generar QR para miembro ID: {id_miembro}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellido FROM miembros WHERE id = ?", (id_miembro,))
        miembro = cursor.fetchone()

        if not miembro:
            logging.warning(f"Generar QR: Miembro ID {id_miembro} no encontrado.")
            return jsonify({"message": "Miembro no encontrado"}), 404
        
        nombre_miembro = secure_filename(miembro['nombre'] or "miembro")
        apellido_miembro = secure_filename(miembro['apellido'] or "")
        
        qr_data = f'{{"miembro_id": {id_miembro}}}' 
        
        img = qrcode.make(qr_data)
        
        base_filename = f"{nombre_miembro}{'-' + apellido_miembro if apellido_miembro else ''}_{id_miembro}"
        qr_filename = f"{base_filename}.png"
        qr_filepath = os.path.join(UPLOAD_FOLDER_QRS, qr_filename) 
        
        img.save(qr_filepath)
        logging.info(f"QR generado y guardado en: {qr_filepath} para miembro ID: {id_miembro}")

        qr_image_url = f"{UPLOAD_URL_PATH_QRS}/{qr_filename}" 

        return jsonify({
            "message": "Código QR generado y guardado exitosamente.",
            "qr_filename": qr_filename,
            "qr_image_url": qr_image_url 
        }), 200

    except sqlite3.Error as e_db:
        logging.error(f"Generar QR: Error de base de datos para miembro ID {id_miembro}: {e_db}")
        return jsonify({"message": "Error de base de datos al generar QR."}), 500
    except Exception as e_general:
        logging.error(f"Generar QR: Error general para miembro ID {id_miembro}: {e_general}")
        return jsonify({"message": f"Error inesperado en el servidor al generar QR: {str(e_general)}"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/miembros/<int:id_miembro>/enviar_qr', methods=['POST'])
def enviar_qr_miembro_api(id_miembro):
    logging.info(f"Solicitud para enviar QR para miembro ID: {id_miembro}")
    try:
        import pywhatkit
    except ImportError:
        logging.error("La biblioteca pywhatkit no está instalada.")
        return jsonify({"message": "Error del servidor: Falta la biblioteca para enviar WhatsApp."}), 500
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellido, telefono FROM miembros WHERE id = ?", (id_miembro,))
        miembro = cursor.fetchone()

        if not miembro:
            logging.warning(f"Enviar QR: Miembro ID {id_miembro} no encontrado.")
            return jsonify({"message": "Miembro no encontrado"}), 404
        
        phone_number = miembro['telefono']
        if not phone_number:
            logging.warning(f"Enviar QR: Miembro ID {id_miembro} no tiene teléfono registrado.")
            return jsonify({"message": "El miembro no tiene un número de teléfono registrado."}), 400

        nombre_miembro = secure_filename(miembro['nombre'] or "miembro")
        apellido_miembro = secure_filename(miembro['apellido'] or "")
        base_filename = f"{nombre_miembro}{'-' + apellido_miembro if apellido_miembro else ''}_{id_miembro}"
        qr_filename = f"{base_filename}.png"
        qr_filepath = os.path.join(UPLOAD_FOLDER_QRS, qr_filename)

        if not os.path.exists(qr_filepath):
            logging.warning(f"Enviar QR: Archivo QR no encontrado en {qr_filepath} para miembro ID {id_miembro}. Generar primero.")
            return jsonify({"message": "Código QR no encontrado. Por favor, genere el QR primero."}), 404
        
        phone_number_international = phone_number
        if not phone_number.startswith('+'):
            phone_number_international = f"+52{phone_number}" 
            logging.info(f"Enviar QR: Formateando número {phone_number} a {phone_number_international}")

        try:
            logging.info(f"Intentando enviar QR ({qr_filepath}) a {phone_number_international}...")
            pywhatkit.sendwhats_image(
                receiver=phone_number_international, img_path=qr_filepath,
                caption=f"Código QR de acceso para el gimnasio. ID: {id_miembro}",
                wait_time=25, tab_close=True, close_time=5 ) 
            logging.info(f"Solicitud de envío de QR a {phone_number_international} realizada.")
            return jsonify({"message": f"Intentando enviar QR a {phone_number_international}. Revisa WhatsApp."}), 200
        except Exception as e_pywhatkit:
            logging.error(f"Error con pywhatkit al enviar imagen {qr_filepath} a {phone_number_international}: {e_pywhatkit}")
            return jsonify({"message": f"Error al intentar enviar el QR por WhatsApp: {str(e_pywhatkit)}"}), 500
    except sqlite3.Error as e_db:
        logging.error(f"Enviar QR: Error de base de datos para miembro ID {id_miembro}: {e_db}")
        return jsonify({"message": "Error de base de datos"}), 500
    except Exception as e_general:
        logging.error(f"Enviar QR: Error general para miembro ID {id_miembro}: {e_general}")
        return jsonify({"message": f"Error inesperado en el servidor: {str(e_general)}"}), 500
    finally:
        if conn:
            conn.close()

# --- IMÁGENES (Endpoints de Imágenes) ---
@app.route('/api/miembros/imagen', methods=['POST'])
def subir_imagen_miembro_api():
    if 'image' not in request.files: return jsonify({"message": "No se encontró el archivo de imagen"}), 400
    file = request.files['image']
    miembro_id_str = request.form.get('miembroId')
    if not miembro_id_str or not miembro_id_str.isdigit(): return jsonify({"message": "ID de miembro válido es requerido"}), 400
    miembro_id = int(miembro_id_str)
    if file.filename == '': return jsonify({"message": "Nombre de archivo vacío"}), 400
    if file and allowed_file(file.filename):
        original_filename, extension = os.path.splitext(file.filename)
        filename_base = secure_filename(f"miembro_{miembro_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
        filename_on_server = filename_base + extension.lower()
        filepath_on_server = os.path.join(UPLOAD_FOLDER_MEMBER_IMAGES, filename_on_server)
        conn = None
        try:
            file.save(filepath_on_server)
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO imagenes_miembros (miembro_id, ruta_imagen) VALUES (?, ?)"
            cursor.execute(sql, (miembro_id, filename_on_server)) 
            conn.commit()
            imagen_id = cursor.lastrowid
            image_url = f"{UPLOAD_URL_PATH_MEMBER_IMAGES}/{filename_on_server}"
            return jsonify({"message": "Imagen subida y guardada exitosamente", "filename": filename_on_server, "imageUrl": image_url, "imagenId": imagen_id}), 201
        except sqlite3.Error as e_db:
            logging.error(f"Error DB al guardar imagen: {e_db}")
            if os.path.exists(filepath_on_server): os.remove(filepath_on_server)
            return jsonify({"message": "Error al guardar la información de la imagen en la base de datos"}), 500
        except Exception as e_file:
            logging.error(f"Error al guardar archivo de imagen: {e_file}")
            return jsonify({"message": f"Error al guardar el archivo: {str(e_file)}"}), 500
        finally:
            if conn: conn.close()
    else:
        return jsonify({"message": "Tipo de archivo no permitido"}), 400

# --- ACCESO (Endpoints de Acceso) ---
@app.route('/api/acceso', methods=['POST'])
def registrar_acceso_api():
    data = request.get_json()
    if not data or 'tipoAcceso' not in data:
        return jsonify({"message": "Datos de acceso incompletos, falta tipoAcceso"}), 400
    miembro_id = data.get('miembroId')
    nombre_miembro_detectado = data.get('nombreMiembroDetectado')
    tipo_acceso = data['tipoAcceso'] 
    metodo_verificacion = data.get('metodoVerificacion', 'desconocido') 
    imagen_id_acceso = data.get('imagenIdAcceso')
    if not miembro_id and metodo_verificacion == 'id_password':
        return jsonify({"message": "ID de miembro es requerido para acceso con contraseña."}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if miembro_id:
            try:
                miembro_id = int(miembro_id)
                cursor.execute("SELECT tipo_acceso FROM accesos WHERE miembro_id = ? ORDER BY fecha_hora_acceso DESC LIMIT 1", (miembro_id,))
                ultimo_acceso = cursor.fetchone()
                if tipo_acceso == 'ingreso':
                    if ultimo_acceso and ultimo_acceso['tipo_acceso'] == 'ingreso':
                        return jsonify({"message": "Acción no permitida: El miembro ya tiene un ingreso registrado sin una salida previa."}), 409 
                elif tipo_acceso == 'salida':
                    if not ultimo_acceso or ultimo_acceso['tipo_acceso'] == 'salida':
                        return jsonify({"message": "Acción no permitida: El miembro no tiene un ingreso registrado o ya registró una salida."}), 409 
                if not nombre_miembro_detectado:
                    cursor.execute("SELECT nombre, apellido FROM miembros WHERE id = ?", (miembro_id,))
                    miembro_info = cursor.fetchone()
                    if miembro_info:
                        nombre_miembro_detectado = f"{miembro_info['nombre']} {miembro_info['apellido']}"
                    else: 
                        nombre_miembro_detectado = f"ID {miembro_id} (No encontrado)"
            except ValueError:
                return jsonify({"message": "ID de miembro inválido para validar secuencia."}), 400
        sql = """
            INSERT INTO accesos (miembro_id, nombre_miembro_detectado, tipo_acceso, metodo_verificacion, imagen_acceso_id) 
            VALUES (?, ?, ?, ?, ?)
        """
        val = (miembro_id if miembro_id else None, nombre_miembro_detectado, tipo_acceso, metodo_verificacion, imagen_id_acceso)
        cursor.execute(sql, val)
        conn.commit()
        acceso_id = cursor.lastrowid
        return jsonify({"message": f"{tipo_acceso.capitalize()} registrado ({metodo_verificacion}) para {nombre_miembro_detectado or 'miembro'}.", "accesoId": acceso_id}), 201
    except sqlite3.Error as e:
        logging.error(f"Error DB registrando acceso: {e}")
        return jsonify({"message": "Error al registrar acceso"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/acceso/reporte', methods=['GET'])
def obtener_reporte_acceso_api():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT 
                a.id as noAcceso,
                strftime('%Y-%m-%d', a.fecha_hora_acceso, 'localtime') as fechaIngreso,
                strftime('%H:%M:%S', a.fecha_hora_acceso, 'localtime') as horaIngreso,
                a.tipo_acceso as estadoAcceso,
                a.miembro_id as idMiembro,
                COALESCE(m.nombre, '') AS nombreMiembroBase, 
                COALESCE(m.apellido, '') AS apellidoMiembroBase,
                a.nombre_miembro_detectado,
                a.metodo_verificacion
            FROM accesos a
            LEFT JOIN miembros m ON a.miembro_id = m.id
            ORDER BY a.fecha_hora_acceso DESC
        """
        cursor.execute(sql)
        reporte_raw = cursor.fetchall()
        reporte_final = []
        for item_raw in reporte_raw:
            item = dict(item_raw)
            if item['idMiembro']:
                item['nombreMiembro'] = f"{item['nombreMiembroBase']} {item['apellidoMiembroBase']}".strip()
            else:
                item['nombreMiembro'] = item['nombre_miembro_detectado'] or "Desconocido"
            item.pop('nombreMiembroBase', None)
            item.pop('apellidoMiembroBase', None)
            item.pop('nombre_miembro_detectado', None)
            reporte_final.append(item)
        return jsonify(reporte_final), 200
    except sqlite3.Error as e:
        logging.error(f"Error DB obteniendo reporte: {e}")
        return jsonify({"message": "Error al obtener reporte de acceso"}), 500
    finally:
        if conn: conn.close()

# --- Endpoint para Descargar Reporte Excel ---
@app.route('/api/acceso/reporte/descargar_excel', methods=['POST'])
def descargar_reporte_excel_api():
    # Importaciones diferidas
    from io import BytesIO
    import openpyxl

    logging.info("Accediendo a endpoint /api/acceso/reporte/descargar_excel")
    data = request.get_json()
    logging.info(f"Datos recibidos para descarga: {data}")

    id_gerente = data.get('idGerente')
    contrasena_gerente = data.get('contrasenaGerente')
    fecha_inicio_str = data.get('fecha_inicio')
    fecha_fin_str = data.get('fecha_fin')

    if not all([id_gerente, contrasena_gerente, fecha_inicio_str, fecha_fin_str]):
        logging.warning("Faltan datos para la descarga del reporte.")
        return jsonify({"message": "Faltan credenciales de gerente o rango de fechas."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logging.info("Validando credenciales de gerente para descarga...")

        query_gerente = "SELECT id, contrasena_hash FROM gerentes WHERE id = ? OR correo = ?"
        params_gerente = (id_gerente,) # Inicializar params
        if not str(id_gerente).isdigit():
             query_gerente = "SELECT id, contrasena_hash FROM gerentes WHERE correo = ?"
        else: 
            params_gerente = (int(id_gerente), id_gerente) # Actualizar params si es ID
            
        cursor.execute(query_gerente, params_gerente)
        gerente = cursor.fetchone()

        if not (gerente and check_password(contrasena_gerente, gerente['contrasena_hash'])):
            logging.warning("Credenciales de gerente inválidas para descarga.")
            return jsonify({"message": "Credenciales de gerente inválidas."}), 401
        
        logging.info("Gerente validado. Obteniendo datos del reporte...")
        sql_reporte = """
            SELECT 
                a.id as noAcceso,
                strftime('%Y-%m-%d', a.fecha_hora_acceso, 'localtime') as fecha,
                strftime('%H:%M:%S', a.fecha_hora_acceso, 'localtime') as hora,
                a.tipo_acceso as estado,
                a.miembro_id as idMiembro,
                COALESCE(m.nombre || ' ' || m.apellido, a.nombre_miembro_detectado, 'Desconocido') as nombreMiembro,
                a.metodo_verificacion as metodo
            FROM accesos a
            LEFT JOIN miembros m ON a.miembro_id = m.id
            WHERE date(a.fecha_hora_acceso, 'localtime') BETWEEN date(?) AND date(?)
            ORDER BY a.fecha_hora_acceso DESC
        """
        cursor.execute(sql_reporte, (fecha_inicio_str, fecha_fin_str))
        registros = cursor.fetchall()
        logging.info(f"Se encontraron {len(registros)} registros para el reporte.")

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Reporte de Accesos"
        headers = ["No. Acceso", "Fecha", "Hora", "Estado", "ID Miembro", "Nombre Miembro", "Método"]
        sheet.append(headers)
        for registro_db in registros:
            sheet.append(list(registro_db)) 
        
        excel_stream = BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)
        filename = f"reporte_accesos_{fecha_inicio_str}_a_{fecha_fin_str}.xlsx"
        logging.info(f"Archivo Excel '{filename}' generado. Enviando para descarga...")
        
        return send_file(
            excel_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except sqlite3.Error as e_db:
        logging.error(f"Error de base de datos al generar reporte Excel: {e_db}")
        return jsonify({"message": "Error de base de datos al generar el reporte."}), 500
    except Exception as e_general:
        logging.error(f"Error general al generar reporte Excel: {e_general}", exc_info=True)
        return jsonify({"message": f"Error inesperado en el servidor: {str(e_general)}"}), 500
    finally:
        if conn:
            conn.close()

# Servir archivos estáticos (como imágenes subidas)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER_MEMBER_IMAGES): # CORREGIDO
        os.makedirs(UPLOAD_FOLDER_MEMBER_IMAGES)
        logging.info(f"Carpeta de subidas de imágenes de miembros creada en: {UPLOAD_FOLDER_MEMBER_IMAGES}")
    if not os.path.exists(UPLOAD_FOLDER_QRS): # CORREGIDO
        os.makedirs(UPLOAD_FOLDER_QRS)
        logging.info(f"Carpeta de QRs creada en: {UPLOAD_FOLDER_QRS}")

    if not os.path.exists(DATABASE_FILE):
        logging.warning(f"El archivo de base de datos '{DATABASE_FILE}' no existe.")
        logging.warning("Por favor, ejecuta 'python backend/setup_db.py' para inicializar la base de datos.")
    
    logging.info(f"Servidor Flask iniciando en el puerto 5000...")
    app.run(debug=True, port=5000) # Considerar use_reloader=False si hay problemas con librerías externas
