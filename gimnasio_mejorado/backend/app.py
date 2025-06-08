# backend/app.py
import os
import sqlite3
import bcrypt
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
import logging
import cv2 # OpenCV
import numpy as np
from PIL import Image
import openpyxl
from io import BytesIO

# Importación para la decodificación de QR
from pyzbar.pyzbar import decode as pyzbar_decode

# Importar la librería para generar QR
import qrcode
# 'pywhatkit' se importará localmente en su función para evitar bloqueos.

# Importar configuración
from db_config import (
    DATABASE_FILE,
    UPLOAD_FOLDER_MEMBER_IMAGES,
    ALLOWED_EXTENSIONS,
    UPLOAD_FOLDER_QRS,
    UPLOAD_URL_PATH_QRS
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s [%(funcName)s]')

app = Flask(__name__, static_folder='static')

CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=['Content-Disposition'])


# --- Configuración OpenCV ---
HAAR_CASCADE_PATH = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
MODELO_LBPH_PATH = os.path.join(os.path.dirname(__file__), 'modelo_lbph.yml')
face_detector = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

# --- Funciones de Ayuda ---
def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con SQLite: {e}")
        raise

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    if not password or not hashed_password:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- GERENTES (Endpoints CRUD Completos) ---
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
        
        if str(id_gerente_input).isdigit():
            query = "SELECT id, nombre, apellido, correo, contrasena_hash FROM gerentes WHERE id = ?"
            params = (int(id_gerente_input),)
        else:
            query = "SELECT id, nombre, apellido, correo, contrasena_hash FROM gerentes WHERE correo = ?"
            params = (id_gerente_input,)
        
        cursor.execute(query, params)
        gerente = cursor.fetchone()

        if gerente and check_password(contrasena, gerente['contrasena_hash']):
            logging.info(f"Gerente validado: {gerente['correo']} (ID: {gerente['id']})")
            return jsonify({
                "message": "Gerente validado exitosamente",
                "idGerente": gerente['id'],
                "nombre": gerente['nombre'],
                "apellido": gerente['apellido'],
                "correo": gerente['correo']
                }), 200
        else:
            logging.warning(f"Intento de validación de gerente fallido para: {id_gerente_input}")
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
        return jsonify({"message": "Error de unicidad al registrar gerente"}), 409
    except sqlite3.Error as e:
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
        allowed_to_update_map = {'nombre': 'nombre', 'apellido': 'apellido', 'telefono': 'telefono', 'correo': 'correo', 'rfc': 'rfc'}
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
        return jsonify({"message": "Error al eliminar gerente"}), 500
    finally:
        if conn: conn.close()

# --- MIEMBROS (Endpoints CRUD Completos) ---
@app.route('/api/miembros', methods=['POST'])
def registrar_miembro_api():
    data = request.get_json()
    required_fields = ['nombre', 'apellido', 'membresia', 'contrasena', 'gerenteId', 'contrasenaGerente']
    if not all(k in data and (data[k] or k in ['telefono', 'correo']) for k in required_fields):
        return jsonify({"message": "Faltan campos requeridos"}), 400
    if len(data['contrasena']) < 6:
        return jsonify({"message": "La contraseña del miembro debe tener al menos 6 caracteres"}), 400
    
    conn = get_db_connection()
    try:
        if str(data['gerenteId']).isdigit():
            gerente = conn.execute("SELECT * FROM gerentes WHERE id = ?", (int(data['gerenteId']),)).fetchone()
        else:
            gerente = conn.execute("SELECT * FROM gerentes WHERE correo = ?", (data['gerenteId'],)).fetchone()
        
        if not (gerente and check_password(data['contrasenaGerente'], gerente['contrasena_hash'])):
            return jsonify({"message": "Credenciales de gerente inválidas"}), 401
        
        hashed_member_pass = hash_password(data['contrasena'])
        fecha_inicio_membresia = datetime.now(timezone.utc).date()
        tipo_membresia = data['membresia']
        dias_map = {"1 Mes": 30, "3 Meses": 90, "6 Meses": 180}
        dias_membresia = dias_map.get(tipo_membresia, 0)
        
        if dias_membresia == 0: return jsonify({"message": "Tipo de membresía inválido"}), 400
        
        fecha_vencimiento_membresia = fecha_inicio_membresia + timedelta(days=dias_membresia)
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO miembros (nombre, apellido, telefono, correo, contrasena_hash, tipo_membresia, fecha_inicio_membresia, fecha_vencimiento_membresia, estado_membresia) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data['nombre'], data['apellido'], data.get('telefono'), data.get('correo'), hashed_member_pass, tipo_membresia, fecha_inicio_membresia, fecha_vencimiento_membresia, 'activa')
        )
        conn.commit()
        miembro_id = cursor.lastrowid
        return jsonify({"message": "Miembro registrado exitosamente", "id": miembro_id, "nombre": data['nombre']}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message": "El correo o teléfono ya están registrados."}), 409
    except Exception as e:
        return jsonify({"message": "Error inesperado en el servidor"}), 500
    finally:
        if conn: conn.close()
    
@app.route('/api/miembros', methods=['GET'])
def obtener_miembros_api():
    conn = get_db_connection()
    try:
        conn.execute("UPDATE miembros SET estado_membresia = 'vencida' WHERE fecha_vencimiento_membresia < date('now', 'localtime') AND estado_membresia = 'activa'")
        conn.commit()
        miembros = conn.execute("SELECT *, strftime('%Y-%m-%d', fecha_vencimiento_membresia) as fechaVencimiento FROM miembros ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in miembros]), 200
    finally:
        conn.close()

@app.route('/api/miembros/<int:id_miembro>', methods=['PUT'])
def actualizar_miembro_api(id_miembro):
    data = request.get_json()
    if not data: return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400
    
    conn = get_db_connection()
    try:
        update_fields, update_values = [], []
        
        allowed_map = {'nombre': 'nombre', 'apellido': 'apellido', 'telefono': 'telefono', 'correo': 'correo'}
        for db_col, json_key in allowed_map.items():
            if json_key in data and data[json_key] is not None:
                update_fields.append(f"{db_col} = ?")
                update_values.append(data[json_key])
        
        if 'contrasena' in data and data['contrasena']:
            if len(data['contrasena']) < 6: return jsonify({"message": "La nueva contraseña debe tener al menos 6 caracteres."}), 400
            update_fields.append("contrasena_hash = ?")
            update_values.append(hash_password(data['contrasena']))

        if 'duracionMembresia' in data and data['duracionMembresia']:
            dias_map = {"1 Mes": 30, "3 Meses": 90, "6 Meses": 180}
            dias = dias_map.get(data['duracionMembresia'])
            if dias:
                inicio = datetime.now(timezone.utc).date()
                vencimiento = inicio + timedelta(days=dias)
                update_fields.extend(["tipo_membresia = ?", "fecha_inicio_membresia = ?", "fecha_vencimiento_membresia = ?", "estado_membresia = ?"])
                update_values.extend([data['duracionMembresia'], inicio, vencimiento, 'activa'])
            else:
                return jsonify({"message": "Duración de membresía inválida."}), 400
        
        elif 'fechaVencimiento' in data and data['fechaVencimiento']:
            try:
                fv = datetime.strptime(data['fechaVencimiento'], '%Y-%m-%d').date()
                estado = 'activa' if fv >= datetime.now(timezone.utc).date() else 'vencida'
                update_fields.extend(["fecha_vencimiento_membresia = ?", "estado_membresia = ?"])
                update_values.extend([data['fechaVencimiento'], estado])
            except ValueError:
                return jsonify({"message": "Formato de fecha inválido. Usar colorChoice-MM-DD."}), 400

        if not update_fields: return jsonify({"message": "No hay campos válidos para actualizar."}), 400
        
        update_values.append(id_miembro)
        sql = f"UPDATE miembros SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(sql, tuple(update_values))
        conn.commit()

        if cursor.rowcount == 0: return jsonify({"message": "Miembro no encontrado o sin cambios."}), 404
        return jsonify({"message": "Miembro actualizado exitosamente"}), 200
    except sqlite3.IntegrityError: return jsonify({"message": "Error: El correo ya existe."}), 409
    except Exception as e: return jsonify({"message": f"Error inesperado: {str(e)}"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/miembros/<int:id_miembro>', methods=['DELETE'])
def eliminar_miembro_api(id_miembro):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM miembros WHERE id = ?", (id_miembro,))
        conn.commit()
        if cursor.rowcount == 0: return jsonify({"message": "Miembro no encontrado"}), 404
        return jsonify({"message": "Miembro eliminado exitosamente"}), 200
    except sqlite3.Error: return jsonify({"message": "Error de base de datos al eliminar."}), 500
    finally:
        if conn: conn.close()

# --- CÓDIGO QR ---
@app.route('/api/miembros/<int:miembro_id>/generar_qr', methods=['POST'])
def generar_qr_api(miembro_id):
    conn = get_db_connection()
    miembro = conn.execute("SELECT id FROM miembros WHERE id = ?", (miembro_id,)).fetchone()
    conn.close()
    if not miembro: return jsonify({"message": "Miembro no encontrado"}), 404

    qr_filename = secure_filename(f"qr_miembro_{miembro_id}.png")
    qr_path = os.path.join(UPLOAD_FOLDER_QRS, qr_filename)
    
    img = qrcode.make(str(miembro['id']))
    img.save(qr_path) # type: ignore
    
    return jsonify({"message": "QR generado.", "qr_image_url": f"/static/uploads/qrs/{qr_filename}"}), 200

@app.route('/api/miembros/<int:miembro_id>/enviar_qr', methods=['POST'])
def enviar_qr_api(miembro_id):
    import pywhatkit # Importación local para evitar bloqueo al inicio
    conn = get_db_connection()
    miembro = conn.execute("SELECT id, nombre, telefono FROM miembros WHERE id = ?", (miembro_id,)).fetchone()
    conn.close()
    if not miembro or not miembro['telefono']:
        return jsonify({"message": "Miembro sin teléfono registrado."}), 404

    telefono_num = f"+52{miembro['telefono']}" if not miembro['telefono'].startswith('+') else miembro['telefono']
    qr_path = os.path.join(UPLOAD_FOLDER_QRS, f"qr_miembro_{miembro_id}.png")

    if not os.path.exists(qr_path):
        return jsonify({"message": "Genere el código QR primero."}), 404

    try:
        caption = f"Hola {miembro['nombre']}, este es tu código QR de acceso. ID: {miembro_id}"
        pywhatkit.sendwhats_image(telefono_num, qr_path, caption) # type: ignore
        return jsonify({"message": "Solicitud de envío de QR procesada."}), 202
    except Exception as e:
        return jsonify({"message": f"Error al enviar el QR: {e}"}), 500

# --- RECONOCIMIENTO FACIAL ---
@app.route('/api/miembros/<int:id_miembro>/enrolar_rostro', methods=['POST'])
def enrolar_rostro_api(id_miembro):
    if 'image' not in request.files: return jsonify({"message": "No se encontró el archivo"}), 400
    file = request.files['image']
    
    filename = file.filename
    if not filename or not allowed_file(filename): return jsonify({"message": "Archivo inválido."}), 400

    try:
        image_stream = file.read()
        np_arr = np.frombuffer(image_stream, np.uint8)
        img_opencv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img_opencv, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0: return jsonify({"message": "No se detectó ningún rostro"}), 400
        if len(faces) > 1: return jsonify({"message": "Se detectó más de un rostro"}), 400

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        extension = os.path.splitext(filename)[1].lower()
        new_filename = secure_filename(f"enroll_{id_miembro}_{timestamp}{extension}")
        path = os.path.join(UPLOAD_FOLDER_MEMBER_IMAGES, new_filename)

        with open(path, 'wb') as f: f.write(image_stream)
        
        conn = get_db_connection()
        conn.execute("INSERT INTO imagenes_miembros (miembro_id, ruta_imagen) VALUES (?, ?)", (id_miembro, new_filename))
        conn.commit()
        conn.close()

        return jsonify({"message": "Imagen de enrolamiento guardada.", "filename": new_filename}), 201
    except Exception as e:
        return jsonify({"message": "Error inesperado en el servidor"}), 500

@app.route('/api/entrenar_reconocimiento_facial', methods=['POST'])
def entrenar_modelo_facial_api():
    image_paths = [os.path.join(UPLOAD_FOLDER_MEMBER_IMAGES, f) for f in os.listdir(UPLOAD_FOLDER_MEMBER_IMAGES) if f.startswith('enroll_')]
    if not image_paths: return jsonify({"message": "No hay imágenes para entrenar."}), 400

    faces, labels = [], []
    for image_path in image_paths:
        try:
            pil_image = Image.open(image_path).convert('L')
            image_np = np.array(pil_image, 'uint8')
            label = int(os.path.basename(image_path).split('_')[1])
            detected = face_detector.detectMultiScale(image_np)
            for (x, y, w, h) in detected:
                faces.append(image_np[y:y+h, x:x+w])
                labels.append(label)
        except Exception:
            continue

    if not faces: return jsonify({"message": "No se detectaron rostros."}), 400

    recognizer = cv2.face.LBPHFaceRecognizer_create() # type: ignore
    recognizer.train(faces, np.array(labels))
    recognizer.write(MODELO_LBPH_PATH)
    return jsonify({"message": "Entrenamiento completado."}), 200

# --- ACCESO ---
@app.route('/api/acceso/verificar_rostro', methods=['POST'])
def verificar_rostro_api():
    if 'image' not in request.files: return jsonify({"message": "No se envió imagen."}), 400
    file = request.files['image']
    filestr = file.read()
    image_color = cv2.imdecode(np.frombuffer(filestr, np.uint8), cv2.IMREAD_COLOR)
    gray_image = cv2.cvtColor(image_color, cv2.COLOR_BGR2GRAY)
    
    miembro_id, metodo = None, None
    if os.path.exists(MODELO_LBPH_PATH):
        recognizer = cv2.face.LBPHFaceRecognizer_create() # type: ignore
        recognizer.read(MODELO_LBPH_PATH)
        faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
        for (x, y, w, h) in faces:
            label, confidence = recognizer.predict(gray_image[y:y+h, x:x+w])
            if confidence < 70:
                miembro_id, metodo = label, 'reconocimiento_facial'
                break
    if not miembro_id:
        decoded = pyzbar_decode(image_color)
        if decoded and decoded[0].data.decode('utf-8').isdigit():
            miembro_id, metodo = int(decoded[0].data.decode('utf-8')), 'qr_code'

    if miembro_id:
        conn = get_db_connection()
        miembro_info = conn.execute("SELECT * FROM miembros WHERE id = ?", (miembro_id,)).fetchone()
        if not miembro_info or miembro_info['estado_membresia'] != 'activa':
            conn.close()
            return jsonify({"accesoPermitido": False, "message": "Miembro no encontrado o inactivo."}), 403
        
        ultimo = conn.execute("SELECT tipo_acceso FROM accesos WHERE miembro_id = ? ORDER BY fecha_hora_acceso DESC LIMIT 1", (miembro_id,)).fetchone()
        conn.close()
        
        tipo_acceso = 'ingreso' if not ultimo or ultimo['tipo_acceso'] == 'salida' else 'salida'
        res, code = registrar_acceso_logica(miembro_id, tipo_acceso, metodo)
        
        if res["success"]:
            return jsonify({"accesoPermitido": True, "message": res['message'], "nombreMiembro": f"{miembro_info['nombre']} {miembro_info['apellido']}", "tipoAccesoRegistrado": tipo_acceso}), code
        else:
            return jsonify({"accesoPermitido": False, "message": res['message']}), code
    else:
        return jsonify({"accesoPermitido": False, "message": "Acceso denegado. No reconocido."}), 401

def registrar_acceso_logica(miembro_id, tipo_acceso, metodo):
    conn = get_db_connection()
    try:
        ultimo = conn.execute("SELECT tipo_acceso FROM accesos WHERE miembro_id = ? ORDER BY fecha_hora_acceso DESC LIMIT 1", (miembro_id,)).fetchone()
        if tipo_acceso == 'ingreso' and ultimo and ultimo['tipo_acceso'] == 'ingreso':
            return {"success": False, "message": "El miembro ya tiene un ingreso sin salida."}, 409
        if tipo_acceso == 'salida' and (not ultimo or ultimo['tipo_acceso'] == 'salida'):
            return {"success": False, "message": "No hay un ingreso previo para registrar una salida."}, 409

        info = conn.execute("SELECT nombre, apellido FROM miembros WHERE id = ?", (miembro_id,)).fetchone()
        nombre = f"{info['nombre']} {info['apellido']}" if info else f"ID {miembro_id}"
        
        conn.execute("INSERT INTO accesos (miembro_id, nombre_miembro_detectado, tipo_acceso, metodo_verificacion) VALUES (?, ?, ?, ?)", (miembro_id, nombre, tipo_acceso, metodo))
        conn.commit()
        return {"success": True, "message": f"{tipo_acceso.capitalize()} registrado."}, 201
    finally:
        conn.close()


# --- REPORTES ---
@app.route('/api/acceso/reporte', methods=['GET'])
def obtener_reporte_acceso_api():
    conn = get_db_connection()
    try:
        sql = """
            SELECT a.id as noAcceso, strftime('%Y-%m-%d', a.fecha_hora_acceso, 'localtime') as fechaIngreso,
                   strftime('%H:%M:%S', a.fecha_hora_acceso, 'localtime') as horaIngreso,
                   COALESCE(a.tipo_acceso, 'desconocido') as estadoAcceso, a.miembro_id as idMiembro,
                   COALESCE(a.nombre_miembro_detectado, 'Desconocido') as nombreMiembro, a.metodo_verificacion
            FROM accesos a ORDER BY a.fecha_hora_acceso DESC
        """
        accesos = conn.execute(sql).fetchall()
        return jsonify([dict(row) for row in accesos])
    finally:
        conn.close()

@app.route('/api/acceso/reporte/descargar_excel', methods=['POST'])
def descargar_reporte_excel_api():
    data = request.get_json()
    id_gerente, contrasena_gerente = data.get('idGerente'), data.get('contrasenaGerente')
    fecha_inicio, fecha_fin = data.get('fecha_inicio'), data.get('fecha_fin')
    if not all([id_gerente, contrasena_gerente, fecha_inicio, fecha_fin]):
        return jsonify({"message": "Faltan credenciales o rango de fechas."}), 400

    conn = get_db_connection()
    try:
        if str(id_gerente).isdigit():
            gerente = conn.execute("SELECT * FROM gerentes WHERE id = ?", (int(id_gerente),)).fetchone()
        else:
            gerente = conn.execute("SELECT * FROM gerentes WHERE correo = ?", (id_gerente,)).fetchone()
        
        if not (gerente and check_password(contrasena_gerente, gerente['contrasena_hash'])):
            return jsonify({"message": "Credenciales de gerente inválidas."}), 401

        sql = """
            SELECT a.id, a.miembro_id, COALESCE(a.nombre_miembro_detectado, 'N/A'), a.tipo_acceso, 
                   strftime('%Y-%m-%d %H:%M:%S', a.fecha_hora_acceso, 'localtime'), a.metodo_verificacion
            FROM accesos a WHERE date(a.fecha_hora_acceso, 'localtime') BETWEEN ? AND ?
            ORDER BY a.fecha_hora_acceso DESC
        """
        registros = conn.execute(sql, (fecha_inicio, fecha_fin)).fetchall()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        
        if ws is not None:
            ws.title = "Reporte de Accesos"
            ws.append(['ID', 'ID Miembro', 'Nombre', 'Tipo', 'Fecha y Hora', 'Método'])
            for reg in registros:
                ws.append(list(reg))
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, download_name=f"reporte_{fecha_inicio}_a_{fecha_fin}.xlsx",
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    finally:
        conn.close()

# --- Servir Archivos Estáticos ---
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER_MEMBER_IMAGES, UPLOAD_FOLDER_QRS]:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(HAAR_CASCADE_PATH):
        logging.error(f"NO SE ENCUENTRA EL ARCHIVO HAAR CASCADE: '{HAAR_CASCADE_PATH}'")
    
    app.run(debug=True, port=5000)
