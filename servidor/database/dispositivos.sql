-- Tabla de dispositivos para FlashCast
-- Requiere PostgreSQL 18+

CREATE TABLE dispositivos (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) NOT NULL UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    departamento VARCHAR(100),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dispositivos_departamento ON dispositivos(departamento);
CREATE INDEX idx_dispositivos_ip ON dispositivos(ip);

-- Trigger para actualizar ultima_actualizacion al modificar
CREATE OR REPLACE FUNCTION actualizar_ultima_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actualizar_ultima_actualizacion
    BEFORE UPDATE ON dispositivos
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_ultima_actualizacion();