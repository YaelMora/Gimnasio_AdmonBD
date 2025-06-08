-- backend/schema.sql

-- Tabla de Gerentes
CREATE TABLE IF NOT EXISTS gerentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    telefono TEXT,
    correo TEXT UNIQUE NOT NULL,
    rfc TEXT UNIQUE,
    contrasena_hash TEXT NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Miembros
CREATE TABLE IF NOT EXISTS miembros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    telefono TEXT,
    correo TEXT UNIQUE,
    contrasena_hash TEXT, 
    fecha_nacimiento DATE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_membresia_actual INTEGER,
    tipo_membresia TEXT, 
    fecha_inicio_membresia DATE,
    fecha_vencimiento_membresia DATE,
    estado_membresia TEXT DEFAULT 'inactiva' 
);

-- Tabla de Imágenes de Miembros (para fotos de perfil y enrolamiento)
CREATE TABLE IF NOT EXISTS imagenes_miembros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    miembro_id INTEGER NOT NULL,
    ruta_imagen TEXT NOT NULL, 
    fecha_captura DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

-- La tabla miembro_encodings_faciales ha sido eliminada.

-- Tabla de Accesos
CREATE TABLE IF NOT EXISTS accesos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    miembro_id INTEGER,
    nombre_miembro_detectado TEXT,
    tipo_acceso TEXT NOT NULL, -- 'ingreso' o 'salida'
    fecha_hora_acceso DATETIME DEFAULT CURRENT_TIMESTAMP,
    metodo_verificacion TEXT, -- 'id_password', 'captura_manual', 'reconocimiento_facial'
    imagen_acceso_id INTEGER, 
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE SET NULL,
    FOREIGN KEY (imagen_acceso_id) REFERENCES imagenes_miembros(id) ON DELETE SET NULL 
);

-- Tabla de Tipos de Membresía
CREATE TABLE IF NOT EXISTS tipos_membresia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    duracion_dias INTEGER NOT NULL,
    precio REAL NOT NULL
);

