USE Gimnasio;
GO

--Registrar un Nuevo Gerente
CREATE PROCEDURE sp_RegistrarGerente (
    @nombre NVARCHAR(100),
    @apellido NVARCHAR(100),
    @telefono NVARCHAR(20),
    @correo NVARCHAR(255),
    @rfc NVARCHAR(20),
    @contrasena_hash NVARCHAR(255)
)
AS
BEGIN
    SET NOCOUNT ON;

    -- Se inserta el nuevo gerente con los datos proporcionados.
    -- La fecha de registro se establece automáticamente por el valor DEFAULT de la tabla.
    INSERT INTO dbo.gerentes (
        nombre,
        apellido,
        telefono,
        correo,
        rfc,
        contrasena_hash
    )
    VALUES (
        @nombre,
        @apellido,
        @telefono,
        @correo,
        @rfc,
        @contrasena_hash
    );

    -- Devuelve el ID del gerente recién creado para confirmación.
    SELECT SCOPE_IDENTITY() AS NuevoGerenteID;
END
GO

--Autenticar a un Gerente
CREATE PROCEDURE sp_AutenticarGerente (
    @correo NVARCHAR(255),
    @contrasena_hash NVARCHAR(255)
)
AS
BEGIN
    SET NOCOUNT ON;

    -- Se busca un gerente que coincida exactamente con el correo y el hash de la contraseña.
    SELECT
        id,
        nombre,
        apellido,
        correo,
        rfc
    FROM
        dbo.gerentes
    WHERE
        correo = @correo
        AND contrasena_hash = @contrasena_hash;

    -- Si la consulta devuelve una fila, la autenticación es exitosa.
    -- Si no devuelve filas, las credenciales son incorrectas.
    -- La aplicación que llama a este SP se encargará de interpretar el resultado.
END
GO