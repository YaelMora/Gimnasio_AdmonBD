use Gimnasio;
GO

-- Tabla de Gerentes
CREATE TABLE gerentes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    apellido NVARCHAR(100) NOT NULL,
    telefono NVARCHAR(20),
    correo NVARCHAR(255) NOT NULL UNIQUE,
    rfc NVARCHAR(20) UNIQUE,
    contrasena_hash NVARCHAR(255) NOT NULL,
    fecha_registro DATETIME DEFAULT GETDATE()
);

-- Tabla de Miembros
CREATE TABLE miembros (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    apellido NVARCHAR(100) NOT NULL,
    telefono NVARCHAR(20),
    correo NVARCHAR(255) UNIQUE,
    contrasena_hash NVARCHAR(255),
    fecha_nacimiento DATE,
    fecha_registro DATETIME DEFAULT GETDATE(),
    id_membresia_actual INT,
    tipo_membresia NVARCHAR(100),
    fecha_inicio_membresia DATE,
    fecha_vencimiento_membresia DATE,
    estado_membresia NVARCHAR(50) DEFAULT 'inactiva'
);

-- Tabla de Imágenes de Miembros
CREATE TABLE imagenes_miembros (
    id INT IDENTITY(1,1) PRIMARY KEY,
    miembro_id INT NOT NULL,
    ruta_imagen NVARCHAR(500) NOT NULL,
    fecha_captura DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_imagenes_miembros_miembro_id FOREIGN KEY (miembro_id)
        REFERENCES miembros(id)
        ON DELETE CASCADE
);

-- Tabla de Accesos corregida
CREATE TABLE accesos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    miembro_id INT,
    nombre_miembro_detectado NVARCHAR(200),
    tipo_acceso NVARCHAR(50) NOT NULL,
    fecha_hora_acceso DATETIME DEFAULT GETDATE(),
    metodo_verificacion NVARCHAR(100),
    imagen_acceso_id INT,
    CONSTRAINT FK_accesos_miembro_id FOREIGN KEY (miembro_id)
        REFERENCES miembros(id)
        ON DELETE SET NULL,
    CONSTRAINT FK_accesos_imagen_acceso_id FOREIGN KEY (imagen_acceso_id)
        REFERENCES imagenes_miembros(id)
        ON DELETE NO ACTION  -- <- Esta es la corrección
);


-- Tabla de Tipos de Membresía
CREATE TABLE tipos_membresia (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL UNIQUE,
    duracion_dias INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL
);
