USE Gimnasio;
GO

CREATE NONCLUSTERED INDEX IX_accesos_fecha_desc_cubierto
ON dbo.accesos (fecha_hora_acceso DESC)
INCLUDE (miembro_id, tipo_acceso, metodo_verificacion);
GO

DROP INDEX IX_accesos_fecha_desc_cubierto ON dbo.accesos;
GO