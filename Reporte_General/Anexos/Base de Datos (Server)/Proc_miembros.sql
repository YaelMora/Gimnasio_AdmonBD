USE Gimnasio;
go

--Ingresar un nuevo usuario
CREATE PROCEDURE sp_RegistrarMiembro (
    @nombre NVARCHAR(100),
    @apellido NVARCHAR(100),
    @telefono NVARCHAR(20),
    @correo NVARCHAR(255),
    @contrasena_hash NVARCHAR(255),
    @fecha_nacimiento DATE
)
AS
BEGIN
    -- Evita que se devuelvan los recuentos de filas afectadas
    SET NOCOUNT ON;

    -- Se inserta el nuevo miembro con los datos proporcionados.
    -- El estado de la membresía por defecto es 'inactiva'.
    INSERT INTO dbo.miembros (
        nombre,
        apellido,
        telefono,
        correo,
        contrasena_hash,
        fecha_nacimiento
    )
    VALUES (
        @nombre,
        @apellido,
        @telefono,
        @correo,
        @contrasena_hash,
        @fecha_nacimiento
    );

    -- Devuelve el ID del miembro recién creado
    SELECT SCOPE_IDENTITY() AS NuevoMiembroID;
END
GO

--Actualizar Membresias
CREATE PROCEDURE sp_ActualizarEstadoMembresias
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @fecha_actual DATE = GETDATE();

    UPDATE dbo.miembros
    SET
        estado_membresia = 'vencida'
    WHERE
        estado_membresia = 'activa'
        AND fecha_vencimiento_membresia < @fecha_actual;
    
    -- Devuelve el número de filas que se actualizaron
    SELECT @@ROWCOUNT AS MembresiasActualizadas;
END
GO

--Asignar o Renovar una Membresía
CREATE PROCEDURE sp_AsignarOrenovarMembresia (
    @miembro_id INT,
    @tipo_membresia_id INT
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @duracion_dias INT;
    DECLARE @nombre_membresia NVARCHAR(100);
    DECLARE @precio DECIMAL(10,2);

    -- Obtener los detalles del tipo de membresía seleccionado
    SELECT
        @duracion_dias = duracion_dias,
        @nombre_membresia = nombre,
        @precio = precio
    FROM
        dbo.tipos_membresia
    WHERE
        id = @tipo_membresia_id;

    -- Si se encontró el tipo de membresía, se procede a actualizar al miembro
    IF (@duracion_dias IS NOT NULL)
    BEGIN
        UPDATE dbo.miembros
        SET
            id_membresia_actual = @tipo_membresia_id,
            tipo_membresia = @nombre_membresia,
            fecha_inicio_membresia = GETDATE(),
            fecha_vencimiento_membresia = DATEADD(day, @duracion_dias, GETDATE()),
            estado_membresia = 'activa'
        WHERE
            id = @miembro_id;
        
        -- Opcional: Podríamos insertar un registro en una tabla de 'pagos' aquí.
        
        SELECT 'Membresía actualizada correctamente' AS Resultado;
    END
    ELSE
    BEGIN
        -- Si el ID del tipo de membresía no existe, se devuelve un error
        SELECT 'Error: El tipo de membresía especificado no existe.' AS Resultado;
    END
END
GO