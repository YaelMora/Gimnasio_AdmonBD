-- Crear la base de datos gimnasio_BD
CREATE DATABASE gimnasio_BD;

-- Seleccionar la base de datos
USE gimnasio_BD;

-- Crear la tabla gerente
CREATE TABLE gerente (
    id_gerente INT AUTO_INCREMENT PRIMARY KEY,  -- Llave primaria
    nombre_g VARCHAR(50) NOT NULL,
    apellido_g VARCHAR(50) NOT NULL,
    telefono_g VARCHAR(15),
    email_g VARCHAR(100),
    RFC VARCHAR(13),
    contraseña_g VARCHAR(100) NOT NULL
);

-- Crear la tabla miembros con una llave foránea a gerente
CREATE TABLE miembros (
    id_miembro INT AUTO_INCREMENT PRIMARY KEY,
    nombre_m VARCHAR(50) NOT NULL,
    apellido_m VARCHAR(50) NOT NULL,
    telefono_m VARCHAR(15),
    email_m VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_venci DATE NOT NULL,
    membresia VARCHAR(50),
    id_gerente INT,  -- Llave foránea a gerente
    CONSTRAINT fk_id_gerente
        FOREIGN KEY (id_gerente) REFERENCES gerente(id_gerente)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Crear la tabla acceso
CREATE TABLE acceso (
    id_acceso INT AUTO_INCREMENT PRIMARY KEY,
    fecha_ingreso DATE NOT NULL,
    hora_ingreso TIME NOT NULL,
    estado_acceso VARCHAR(50),  
    id_miembro INT,
    FOREIGN KEY (id_miembro) REFERENCES miembros(id_miembro)  
);

CREATE TABLE admin (
    id_admin INT NOT NULL,
    contraseña_admin VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_admin)
);

INSERT INTO admin (id_admin, contraseña_admin)
VALUES (1, '123');



