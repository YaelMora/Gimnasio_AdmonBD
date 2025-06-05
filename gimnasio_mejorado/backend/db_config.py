# backend/db_config.py
import os

# Directorio base del backend
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Carpeta de instancia para la BD
INSTANCE_FOLDER = os.path.join(BASE_DIR, 'instance')
DATABASE_FILE = os.path.join(INSTANCE_FOLDER, 'gym.db')

# Para la subida de imágenes de miembros
UPLOAD_FOLDER_MEMBER_IMAGES = os.path.join(BASE_DIR, 'static', 'uploads', 'member_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Nueva carpeta para guardar los códigos QR generados
UPLOAD_FOLDER_QRS = os.path.join(BASE_DIR, 'static', 'uploads', 'qrs') # Nueva línea

# Crear carpetas si no existen
if not os.path.exists(INSTANCE_FOLDER):
    try:
        os.makedirs(INSTANCE_FOLDER)
        print(f"Carpeta de instancia creada en: {INSTANCE_FOLDER}")
    except OSError as e:
        print(f"Error creando carpeta de instancia {INSTANCE_FOLDER}: {e}")

if not os.path.exists(UPLOAD_FOLDER_MEMBER_IMAGES):
    try:
        os.makedirs(UPLOAD_FOLDER_MEMBER_IMAGES)
        print(f"Carpeta de subidas de imágenes de miembros creada en: {UPLOAD_FOLDER_MEMBER_IMAGES}")
    except OSError as e:
        print(f"Error creando carpeta de subidas {UPLOAD_FOLDER_MEMBER_IMAGES}: {e}")

if not os.path.exists(UPLOAD_FOLDER_QRS): # Nueva sección
    try:
        os.makedirs(UPLOAD_FOLDER_QRS)
        print(f"Carpeta de QRs creada en: {UPLOAD_FOLDER_QRS}")
    except OSError as e:
        print(f"Error creando carpeta de QRs {UPLOAD_FOLDER_QRS}: {e}")


# URLs base para acceder a los archivos subidos desde el frontend
BASE_STATIC_URL = '/static' 
UPLOAD_URL_PATH_MEMBER_IMAGES = os.path.join(BASE_STATIC_URL, 'uploads', 'member_images').replace("\\", "/")
UPLOAD_URL_PATH_QRS = os.path.join(BASE_STATIC_URL, 'uploads', 'qrs').replace("\\", "/") # Nueva línea

# Cambiar UPLOAD_FOLDER a UPLOAD_FOLDER_MEMBER_IMAGES en el resto del código donde se suben imágenes de miembros
# Para mantener la consistencia, usaremos UPLOAD_FOLDER_MEMBER_IMAGES cuando nos refiramos a las imágenes de los miembros
# y UPLOAD_FOLDER_QRS para los códigos QR.
