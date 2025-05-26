# app.py

from flask import Flask, jsonify, render_template, request, redirect, url_for
from datetime import datetime, timedelta, time
from config import Config, mysql
import os
import cv2
import imutils
import numpy as np
import time


app = Flask(__name__)
app.config.from_object(Config)
mysql.init_app(app)

#Inicio del Sistema
@app.route('/')
def index():
    return render_template('index.html')



#Proceso de Toma Imagenes
@app.route('/toma_imagenes', methods=['GET'])
def toma_imagenes():
    nombre = request.args.get('nombre', 'Nombre por defecto')
    id_miembro = request.args.get('id_miembro')
    return render_template('toma_imagenes.html', nombre=nombre, id_miembro=id_miembro)

#Captura de Imagenes
@app.route('/capture', methods=['POST'])
def capture():
    personName = request.form['id_miembro']
    print('ID: ', personName)
    capturar_imagenes(personName)
    entrenar_modelo_route()
    print("Imágenes capturadas exitosamente.")
    return render_template('toma_imagenes.html', registro=True)  # Redirigir con alerta

#Captura de Imagenes para el Reconocimiento Facial
def capturar_imagenes(personName):
    try:
        #dataPath = 'C:/Users/kivo/Desktop/Nueva carpeta/prototipo gimnasio/miembros/Data'
        
        #personPath = os.path.join(dataPath, personName)
        
        basePath = os.path.dirname(os.path.abspath(__file__))  # Ruta del script actual
        dataPath = os.path.join(basePath, 'miembros', 'Data')  # Ruta relativa para 'miembros/Data'
        personPath = os.path.join(dataPath, str(personName))
        

        if not os.path.exists(personPath):
            print('Carpeta creada: ', personName)
            os.makedirs(personPath)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        haarcascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

        faceClassif = cv2.CascadeClassifier(haarcascade_path)
        if faceClassif.empty():
            print("Error al cargar el clasificador Haar Cascade.")
            return "Error: el archivo Haar Cascade está vacío o no se cargó correctamente."

        count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error al capturar el frame de la cámara.")
                break
            frame = imutils.resize(frame, width=640)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            auxFrame = frame.copy()

            faces = faceClassif.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                rostro = auxFrame[y:y + h, x:x + w]
                rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(os.path.join(personPath, f'rostro_{count}.jpg'), rostro)
                count += 1
            
            cv2.imshow('frame', frame)

            k = cv2.waitKey(1)
            if k == 27 or count >= 300:
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error: {str(e)}")
        return "registro.html"  # Redirigir al template en caso de error
    
#Proceso de Entrenamiento
@app.route('/entrenar_modelo', methods=['POST'])
def entrenar_modelo_route():
    resultado = entrenar_modelo()
    return resultado

#Entrenar Modelo
def entrenar_modelo():
    basePath = os.path.dirname(os.path.abspath(__file__))  # Ruta del script actual
    dataPath = os.path.join(basePath, 'miembros', 'Data')  # Ruta relativa para 'miembros/Data'
    
    #dataPath = 'C:/Users/kivo/Desktop/Nueva carpeta/prototipo gimnasio/miembros/Data'  # Cambia a la ruta donde hayas almacenado Data
    peopleList = os.listdir(dataPath)
    print('Lista de personas: ', peopleList)

    labels = []
    facesData = []
    label = 0

    for nameDir in peopleList:
        personPath = os.path.join(dataPath, nameDir)
        print('Leyendo las imágenes')

        for fileName in os.listdir(personPath):
            
            labels.append(label)
            facesData.append(cv2.imread(os.path.join(personPath, fileName), 0))
        label += 1

    # Métodos para entrenar el reconocedor
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Entrenando el reconocedor de rostros
    print("Entrenando...")
    face_recognizer.train(facesData, np.array(labels))

    # Almacenando el modelo obtenido

    modelPath = os.path.join(basePath, 'modeloLBPHFace.xml')  # Ruta dinámica para almacenar el modelo
    face_recognizer.write(modelPath)

    print("Modelo almacenado correctamente.")
    return "Modelo entrenado y almacenado exitosamente."



#Apartado Reconocimiento
@app.route('/reconocimiento')
def reconocimiento():
    return render_template('reconocimiento.html')

@app.route('/reconocer', methods=['POST'])
def reconoce():
    try:
        status = request.form['status']
        
        basePath = os.path.dirname(os.path.abspath(__file__))  
        dataPath = os.path.join(basePath, 'miembros', 'Data')  
        
        # Verificar si la carpeta de datos existe
        if not os.path.exists(dataPath):
            raise FileNotFoundError(f"La ruta {dataPath} no existe.")
        
        imagePaths = os.listdir(dataPath)
        print('imagePaths=', imagePaths)

        modelPath = os.path.join(basePath, 'modeloLBPHFace.xml')
        
        # Verificar si el modelo existe
        if not os.path.exists(modelPath):
            raise FileNotFoundError(f"El archivo del modelo {modelPath} no fue encontrado.")

        # Cargar el modelo
        face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_recognizer.read(modelPath)
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        recognized_id = None
        start_time = None
        desconocido_start_time = None
        recognition_duration = 4  # Duración del reconocimiento continuo en segundos
        desconocido_duration = 4  # Duración para considerar a un "Desconocido" en segundos

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            auxFrame = gray.copy()

            faces = faceClassif.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                rostro = auxFrame[y:y+h, x:x+w]
                rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
                result = face_recognizer.predict(rostro)

                if result[1] < 58:
                    recognized_person = imagePaths[result[0]]
                    nombre_persona = obtener_nombre_persona(recognized_person)
                    if nombre_persona:
                        cv2.putText(frame, '{}'.format(nombre_persona), (x, y-25), 2, 1.1, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    if recognized_id == recognized_person:
                        if start_time is None:
                            start_time = time.time()
                        else:
                            elapsed_time = time.time() - start_time
                            if elapsed_time >= recognition_duration:
                                print(f"{nombre_persona} ha sido reconocido continuamente durante {recognition_duration} segundos.")
                                registrar_acceso(recognized_person, status)
                                cap.release()
                                cv2.destroyAllWindows()
                                mensaje_registro = f"{status} de {nombre_persona} ha sido registrado exitosamente."
                                return render_template('reconocimiento.html', registro=True, mensaje_registro=mensaje_registro)  # Redirigir con alerta de registro exitoso
                    else:
                        recognized_id = recognized_person
                        start_time = time.time()
                        desconocido_start_time = None  # Reiniciar el contador de "Desconocido"

                else:
                    cv2.putText(frame, 'Desconocido', (x, y-20), 2, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    recognized_id = None
                    start_time = None
                    if desconocido_start_time is None:
                        desconocido_start_time = time.time()
                    else:
                        desconocido_elapsed_time = time.time() - desconocido_start_time
                        if desconocido_elapsed_time >= desconocido_duration:
                            print(f"Desconocido ha sido detectado continuamente durante {desconocido_duration} segundos.")
                            cap.release()
                            cv2.destroyAllWindows()
                            return render_template('reconocimiento.html', alerta=True)  # Redirigir con alerta

            cv2.imshow('frame', frame)
            k = cv2.waitKey(1)
            if k == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        return redirect(url_for('index'))

    except Exception as e:
        print(f"Error durante el reconocimiento: {str(e)}")
        return render_template('reconocimiento.html', error=str(e))  # Redirigir a 'reconocimiento.html' con el mensaje de error


# Obtener el Nombre de la persona
def obtener_nombre_persona(id_persona):
        try:
            # Crear cursor para conectar con la BD
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para insertar el nuevo miembro en la BD
            cur.execute("SELECT nombre_m FROM miembros WHERE id_miembro = %s", (id_persona,))

            record = cur.fetchone()
            if record:
                return record[0]  # Devuelve el primer campo del registro (en este caso, el nombre)
            else:
                return None

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la inserción
            print(f"Error al obtener el nombre: {str(e)}")
            mysql.connection.rollback()  
            return "Error al obtener el nombre. Inténtelo nuevamente."
        
        finally:
            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

# Realizar registro de Acceso
def registrar_acceso(id_persona,status):
        id_persona = id_persona
        fecha_ingreso = datetime.now().date()
        hora_ingreso = datetime.now().time()
        estado_acceso = status
        
        try:
            # Crear cursor para conectar con la BD
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para insertar el nuevo acceso en la BD
            cur.execute("INSERT INTO acceso (fecha_ingreso, hora_ingreso, estado_acceso, id_miembro) VALUES (%s, %s, %s, %s)",
                        (fecha_ingreso, hora_ingreso, estado_acceso, id_persona))
            
             # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()
            return "Acceso registrado correctamente."

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la inserción
            print(f"Error al insertar el acceso: {str(e)}")
            mysql.connection.rollback()  
            return "Error al registrar el acceso. Inténtelo nuevamente."


# Realizar registro de Acceso
def registrar_acceso(id_persona,status):
        id_persona = id_persona
        fecha_ingreso = datetime.now().date()
        hora_ingreso = datetime.now().time()
        estado_acceso = status
        
        try:
            # Crear cursor para conectar con la BD
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para insertar el nuevo acceso en la BD
            cur.execute("INSERT INTO acceso (fecha_ingreso, hora_ingreso, estado_acceso, id_miembro) VALUES (%s, %s, %s, %s)",
                        (fecha_ingreso, hora_ingreso, estado_acceso, id_persona))
            
             # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()
            return "Acceso registrado correctamente."

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la inserción
            print(f"Error al insertar el acceso: {str(e)}")
            mysql.connection.rollback()  
            return "Error al registrar el acceso. Inténtelo nuevamente."




# Reporte de Acceso
@app.route('/reporte', methods=['GET', 'POST'])
def reporte_accesos():
    try:
        # Crear cursor para conectar con la BD
        cur = mysql.connection.cursor()

        # Obtener el nombre a buscar si se ha enviado
        nombre_busqueda = request.form.get('nombre_busqueda')

        # Consultar según el nombre o todos si no hay búsqueda
        if nombre_busqueda:
            cur.execute("""
            SELECT acceso.id_acceso, acceso.fecha_ingreso, acceso.hora_ingreso, acceso.estado_acceso, acceso.id_miembro, miembros.nombre_m, miembros.apellido_m
            FROM acceso
            JOIN miembros ON acceso.id_miembro = miembros.id_miembro
            WHERE miembros.nombre_m LIKE %s
            ORDER BY miembros.nombre_m DESC
            """, ('%' + nombre_busqueda + '%',))  # % para hacer la búsqueda más flexible
        else:
            cur.execute("""
            SELECT acceso.id_acceso, acceso.fecha_ingreso, acceso.hora_ingreso, acceso.estado_acceso, acceso.id_miembro, miembros.nombre_m, miembros.apellido_m
            FROM acceso
            JOIN miembros ON acceso.id_miembro = miembros.id_miembro
            ORDER BY miembros.nombre_m DESC
            """)

        accesos = cur.fetchall()

        # Cerrar cursor
        cur.close()
    
        # Renderizar la plantilla HTML con los registros de acceso
        return render_template('acceso.html', accesos=accesos)

    except Exception as e:
        # Manejar cualquier excepción que pueda ocurrir durante la consulta
        print(f"Error al consultar acceso: {str(e)}")
        mysql.connection.rollback()  
        return "Error al consultar acceso. Inténtelo nuevamente."




#Apartado de Registro
# Método para calcular la fecha de vencimiento de la membresía
def calcular_fecha_vencimiento(membresia):
    fecha_inicio = datetime.now()
    if membresia == '1mes':
        fecha_venci = fecha_inicio + timedelta(days=30)
    elif membresia == '3meses':
        fecha_venci = fecha_inicio + timedelta(days=92)
    elif membresia == '6meses':
        fecha_venci = fecha_inicio + timedelta(days=184)
    else:
        fecha_venci = fecha_inicio  # Manejo de error o caso por defecto
    return fecha_venci

# Ruta y render para el formulario de registro de miembro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_m = request.form['nombre_m']
        apellido_m = request.form['apellido_m']
        telefono_m = request.form['telefono_m']
        email_m = request.form['email_m']
        membresia = request.form['membresia']
        fk_id_gerente = request.form['fk_id_gerente']

        fecha_inicio = datetime.now()
        fecha_venci = calcular_fecha_vencimiento(membresia)
        membresia = "vigente"

        try:
            # Crear cursor para conectar con la BD
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para insertar el nuevo miembro en la BD
            cur.execute("INSERT INTO miembros (nombre_m, apellido_m, telefono_m, email_m, fecha_inicio, fecha_venci, membresia, id_gerente) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (nombre_m, apellido_m, telefono_m, email_m, fecha_inicio, fecha_venci, membresia, fk_id_gerente))

            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Obtener el id_miembro del registro insertado
            id_miembro = cur.lastrowid

            # Cerrar cursor
            cur.close()

            # Redirigir a la toma de imágenes con el nombre del nuevo miembro
            return redirect(url_for('toma_imagenes', nombre=nombre_m, id_miembro=id_miembro))

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la inserción
            print(f"Error al insertar el miembro: {str(e)}")
            mysql.connection.rollback()  
            return "Error al registrar el miembro. Inténtelo nuevamente."

    # Renderizar el formulario de registro para el método GET
    return render_template('registro.html')

# Ruta para confirmar el alta con las credenciales del gerente
@app.route('/validar_gerente', methods=['POST'])
def validar_gerente():
    data = request.get_json()
    gerente_id = data['gerente_id']
    gerente_contraseña = data['gerente_contraseña']

    try:
        # Crear cursor
        cur = mysql.connection.cursor()

        # Obtener la contraseña del gerente por su ID
        cur.execute("SELECT id_gerente, contraseña_g FROM gerente WHERE id_gerente = %s", (gerente_id,))
        gerente = cur.fetchone()

        cur.close()

        if gerente:
            stored_password = gerente[1]  # Contraseña almacenada en la base de datos

            # Verificar si la contraseña ingresada coincide con la almacenada
            if gerente_contraseña == stored_password:
                return jsonify({'success': True, 'id_gerente': gerente[0]})
            else:
                return jsonify({'success': False})  # Contraseña incorrecta
        else:
            return jsonify({'success': False})  # Gerente no encontrado

    except Exception as e:
        print(f"Error al validar las credenciales del gerente: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

    


# Ruta para el formulario de Registro de Gerente
@app.route('/registro_g', methods=['GET', 'POST'])
def registro_g():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_g = request.form['nombre_g']
        apellido_g = request.form['apellido_g']
        telefono_g = request.form['telefono_g']
        email_g = request.form['email_g']
        rfc = request.form['RFC']
        contraseña_g = request.form['contraseña_g']
        confirmar_contraseña_g = request.form['confirmar_contraseña_g']  # Obtener confirmación

        # Validar que las contraseñas coinciden (opcional, ya que ya lo hiciste en JS)
        if contraseña_g != confirmar_contraseña_g:
            return "Las contraseñas no coinciden."

        try:
            # Crear cursor
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para insertar el nuevo gerente en la base de datos
            cur.execute("INSERT INTO gerente (nombre_g, apellido_g, telefono_g, email_g, RFC, contraseña_g) VALUES (%s, %s, %s, %s, %s, %s)",
                        (nombre_g, apellido_g, telefono_g, email_g, rfc, contraseña_g))

            # Confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

            # Redirigir a la página de administración
            return redirect(url_for('admin_gerente'))

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la inserción
            print(f"Error al insertar el gerente: {str(e)}")
            mysql.connection.rollback()  # Hacer rollback en caso de error
            return "Error al registrar el gerente. Inténtelo nuevamente."

    # Renderizar el formulario de registro para el método GET
    return render_template('registro_g.html')



# Ruta para confirmar el alta con las credenciales del admin
@app.route('/validar_admin', methods=['POST'])
def validar_admin():
    data = request.get_json()
    admin_contraseña = data['admin_contraseña']  # Obtener la contraseña desde el formulario

    try:
        # Crear cursor
        cur = mysql.connection.cursor()

        # Ejecutar la consulta SQL para comparar la contraseña con la almacenada en la tabla admin
        cur.execute("SELECT id_admin FROM admin WHERE contraseña_admin = %s", (admin_contraseña,))
        admin = cur.fetchone()

        cur.close()

        if admin:
            # Si la contraseña coincide, devolver éxito
            return jsonify({'success': True, 'id_admin': admin[0]})
        else:
            # Si no coincide, devolver fallo
            return jsonify({'success': False})

    except Exception as e:
        print(f"Error al validar las credenciales del admin: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Ruta para Administrar los Miembros
@app.route('/admin_miem', methods=['GET', 'POST'])
def admin_miembros():
    try:
        # Crear cursor
        cur = mysql.connection.cursor()
        
        if request.method == 'POST':
            # Obtener el término de búsqueda
            busqueda = request.form.get('busqueda')
            # Ejecutar consulta SQL para buscar miembros por nombre o apellido
            query = """
                SELECT id_miembro, nombre_m, apellido_m, telefono_m, email_m, fecha_inicio, fecha_venci, membresia
                FROM miembros
                WHERE nombre_m LIKE %s OR apellido_m LIKE %s
            """
            cur.execute(query, ('%' + busqueda + '%', '%' + busqueda + '%'))
        else:
            # Ejecutar consulta SQL para obtener todos los miembros si no hay búsqueda
            cur.execute("""
                SELECT id_miembro, nombre_m, apellido_m, telefono_m, email_m, fecha_inicio, fecha_venci, membresia
                FROM miembros
            """)

        # Obtener resultados
        miembros = cur.fetchall()

        # Cerrar cursor
        cur.close()

        return render_template('admin_miem.html', miembros=miembros)

    except Exception as e:
        # Manejar cualquier excepción que pueda ocurrir al obtener los datos
        print(f"Error al obtener datos de los miembros: {str(e)}")
        return "Error al cargar la página de administración de miembros"




# Ruta para Administrar los Gerentes
@app.route('/admin_gerente', methods=['GET'])
def admin_gerente():
    try:
        # Crear cursor
        cur = mysql.connection.cursor()
        
        # Obtener el valor de búsqueda, si existe
        nombre_buscado = request.args.get('buscar', None)

        # Si hay un nombre a buscar, ajustar la consulta
        if nombre_buscado:
            query = "SELECT id_gerente, nombre_g, apellido_g, telefono_g, email_g, RFC FROM gerente WHERE nombre_g LIKE %s"
            cur.execute(query, ('%' + nombre_buscado + '%',))
        else:
            # Ejecutar consulta SQL para obtener todos los gerentes
            cur.execute("SELECT id_gerente, nombre_g, apellido_g, telefono_g, email_g, RFC FROM gerente")
        
        gerentes = cur.fetchall()

        # Cerrar cursor
        cur.close()

        return render_template('admin_gerente.html', gerentes=gerentes)

    except Exception as e:
        # Manejar cualquier excepción que pueda ocurrir al obtener los datos
        print(f"Error al obtener datos de los gerentes: {str(e)}")
        return "Error al cargar la página de administración de empleados"



# Ruta para Eliminar un Gerente
@app.route('/eliminar_g/<int:gerente_id>', methods=['POST'])
def eliminar_gerente(gerente_id):
    if request.method == 'POST':
        # Obtener datos del formulario
        confirmacion = request.form['confirmacion']

        # Verificar la confirmación del director
        if confirmacion != 'admin':
            return "Confirmación incorrecta. No se puede eliminar."

        try:
            # Crear cursor
            cur = mysql.connection.cursor()

            # Ejecutar la consulta SQL para eliminar el gerente
            cur.execute("DELETE FROM gerente WHERE id_gerente = %s", (gerente_id,))

            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

            return render_template('admin_gerente.html', eliminar=True)  # Redirigir con alerta

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la eliminación
            print(f"Error al eliminar el gerente: {str(e)}")
            mysql.connection.rollback()  # Hacer rollback en caso de error
            return "Error al eliminar el gerente. Inténtelo nuevamente."



#formulario de Cambio de Gerente
@app.route('/cambios_g/<int:gerente_id>', methods=['GET'])
def cambios_g(gerente_id):
    try:
        # Crear cursor
        cur = mysql.connection.cursor()

        # Obtener datos del gerente según el id_gerente
        cur.execute("SELECT * FROM gerente WHERE id_gerente = %s", (gerente_id,))
        gerente = cur.fetchone()

        # Cerrar cursor
        cur.close()

        if gerente:
            # Renderizar el formulario de cambios con los datos del gerente
            return render_template('cambios_g.html', gerente=gerente)
        else:
            return "Gerente no encontrado"

    except Exception as e:
        print(f"Error al obtener el gerente para editar: {str(e)}")
        return "Error al cargar la página de cambios"

#Actualizar los Datos de Gerente en BD
@app.route('/actualizar_gerente/<int:gerente_id>', methods=['POST'])
def actualizar_gerente(gerente_id):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        rfc = request.form['rfc']

        try:
            # Crear cursor
            cur = mysql.connection.cursor()

            # Ejecutar consulta SQL para actualizar el gerente
            cur.execute("UPDATE gerente SET nombre_g = %s, apellido_g = %s, telefono_g = %s, email_g = %s, RFC = %s WHERE id_gerente = %s",
                        (nombre, telefono, email, rfc, gerente_id))

            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

            # Redirigir de vuelta a la página de administración de gerentes
            return render_template('admin_gerente.html', actualizar=True)  # Redirigir con alerta

        except Exception as e:
            print(f"Error al actualizar el gerente: {str(e)}")
            # Manejar cualquier excepción que pueda ocurrir durante la actualización
            return "Error al actualizar el gerente. Inténtelo nuevamente."



#formulario de Cambio de Miembros
@app.route('/cambios_m/<int:miembro_id>', methods=['GET'])
def cambios_m(miembro_id):
    try:
        # Crear cursor
        cur = mysql.connection.cursor()

        # Obtener datos del gerente según el id_gerente
        cur.execute("SELECT * FROM miembros WHERE id_miembro = %s", (miembro_id,))
        miembro = cur.fetchone()

        # Cerrar cursor
        cur.close()

        if miembro:
            # Renderizar el formulario de cambios con los datos del gerente
            return render_template('cambios_m.html', miembro=miembro)
        else:
            return "Miembro no encontrado"

    except Exception as e:
        print(f"Error al obtener el miembro para editar: {str(e)}")
        return "Error al cargar la página de cambios"

#Actualizar los Datos de Miembro en BD
@app.route('/actualizar_miembro/<int:miembro_id>', methods=['POST'])
def actualizar_miembro(miembro_id):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        fecha = request.form['fecha']
        membresia = request.form['membresia']  # Obtener la membresía seleccionada
        nueva_fecha = actualizar_fecha_vencimiento(membresia,fecha)  # Calcular la nueva fecha de vencimiento

        try:
            # Crear cursor
            cur = mysql.connection.cursor()

            # Ejecutar consulta SQL para actualizar el miembro
            cur.execute("UPDATE miembros SET nombre_m = %s, apellido_m = %s, telefono_m = %s, email_m = %s, fecha_venci = %s WHERE id_miembro = %s",
                        (nombre, apellido, telefono, email, nueva_fecha, miembro_id))

            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

            # Redirigir de vuelta a la página de administración de Miembros
            return render_template('admin_miem.html', actualizar=True)  # Redirigir con alerta

        except Exception as e:
            print(f"Error al actualizar el miembro: {str(e)}")
            # Manejar cualquier excepción que pueda ocurrir durante la actualización
            return "Error al actualizar el miembro. Inténtelo nuevamente."
        
# Método para calcular la fecha de vencimiento de la membresía (Actualizar)
def actualizar_fecha_vencimiento(membresia,fecha):
    fecha_inicio = datetime.strptime(fecha, '%Y-%m-%d')  # Asume que la fecha viene en formato 'YYYY-MM-DD'
    if membresia == '0mes':
        fecha_venci = fecha_inicio + timedelta(days=0)
    elif membresia == '1mes':
        fecha_venci = fecha_inicio + timedelta(days=30)
    elif membresia == '3meses':
        fecha_venci = fecha_inicio + timedelta(days=92)
    elif membresia == '6meses':
        fecha_venci = fecha_inicio + timedelta(days=184)
    else:
        fecha_venci = fecha_inicio  # Manejo de error o caso por defecto
    return fecha_venci


import shutil
# Ruta para Eliminar un Miembro
@app.route('/eliminar_m/<int:miembro_id>', methods=['POST'])
def eliminar_miembro(miembro_id):
    if request.method == 'POST':
        # Obtener datos del formulario
        confirmacion = request.form['confirmacion']

        # Verificar la confirmación del director
        if confirmacion != 'admin':
            return "Confirmación incorrecta. No se puede eliminar."

        try:
            # Crear cursor
            cur = mysql.connection.cursor()

            # Eliminar registros relacionados en la tabla 'acceso'
            cur.execute("DELETE FROM acceso WHERE id_miembro = %s", (miembro_id,))

            # Ejecutar la consulta SQL para eliminar al Miembro
            cur.execute("DELETE FROM miembros WHERE id_miembro = %s", (miembro_id,))

            # Commit para confirmar la transacción
            mysql.connection.commit()

            # Cerrar cursor
            cur.close()

            # Eliminar la carpeta del miembro
            dataPath = f'D:/Reconocimiento facial/reconocimientofacial-main/IA usuarios/Data/{miembro_id}'
            if os.path.exists(dataPath):
                shutil.rmtree(dataPath)

            # Volver a entrenar el modelo
            entrenar_modelo()

            return render_template('admin_miem.html', eliminar=True)  # Redirigir con alerta

        except Exception as e:
            # Manejar cualquier excepción que pueda ocurrir durante la eliminación
            print(f"Error al eliminar al miembro: {str(e)}")
            mysql.connection.rollback()  # Hacer rollback en caso de error
            return "Error al eliminar al miembro. Inténtelo nuevamente."

haarcascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'


if __name__ == "__main__":
    app.run(debug=True)
