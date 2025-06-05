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
    contrasena_hash TEXT, -- NUEVO CAMPO PARA CONTRASEÑA DE MIEMBRO
    fecha_nacimiento DATE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_membresia_actual INTEGER,
    tipo_membresia TEXT, 
    fecha_inicio_membresia DATE,
    fecha_vencimiento_membresia DATE,
    estado_membresia TEXT DEFAULT 'inactiva' 
);

-- Tabla de Imágenes de Miembros
CREATE TABLE IF NOT EXISTS imagenes_miembros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    miembro_id INTEGER NOT NULL,
    ruta_imagen TEXT NOT NULL, 
    fecha_captura DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

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

-- Insertar algunos tipos de membresía base (opcional)
-- INSERT INTO tipos_membresia (nombre, duracion_dias, precio) VALUES
-- ('1 Mes', 30, 500.00),
-- ('3 Meses', 90, 1350.00),
-- ('6 Meses', 180, 2500.00);
