-- init.sql
-- Creación de tablas para el sistema de citas veterinarias

-- Tabla de usuarios (veterinarios y clientes)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL CHECK (role IN ('veterinarian', 'client')),
    specialization VARCHAR(100), -- Solo para veterinarios
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de mascotas (para clientes)
CREATE TABLE IF NOT EXISTS pets (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL,
    breed VARCHAR(100),
    age INTEGER,
    weight DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de disponibilidad de veterinarios
CREATE TABLE IF NOT EXISTS veterinarian_availability (
    id SERIAL PRIMARY KEY,
    veterinarian_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(veterinarian_id, day_of_week, start_time)
);

-- Tabla de citas
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    veterinarian_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    pet_id INTEGER REFERENCES pets(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no-show')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(veterinarian_id, appointment_date, appointment_time)
);

-- Tabla de notificaciones
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('email', 'web', 'both')),
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_client ON appointments(client_id);
CREATE INDEX idx_appointments_veterinarian ON appointments(veterinarian_id);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_pets_owner ON pets(owner_id);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pets_updated_at BEFORE UPDATE ON pets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Datos de ejemplo
INSERT INTO users (email, password, first_name, last_name, phone, role, specialization) VALUES
    ('vet1@veterinary.com', '123', 'Dr. Juan', 'García', '555-0101', 'veterinarian', 'Cirugía General'),
    ('vet2@veterinary.com', '$2b$12$dummy.password.hash', 'Dra. María', 'López', '555-0102', 'veterinarian', 'Medicina Interna'),
    ('client1@email.com', '$2b$12$dummy.password.hash', 'Carlos', 'Rodríguez', '555-0201', 'client', NULL),
    ('client2@email.com', '$2b$12$dummy.password.hash', 'Ana', 'Martínez', '555-0202', 'client', NULL);

-- Disponibilidad de veterinarios (Lunes a Viernes, 9:00-17:00)
INSERT INTO veterinarian_availability (veterinarian_id, day_of_week, start_time, end_time) VALUES
    (1, 1, '09:00', '17:00'),
    (1, 2, '09:00', '17:00'),
    (1, 3, '09:00', '17:00'),
    (1, 4, '09:00', '17:00'),
    (1, 5, '09:00', '17:00'),
    (2, 1, '09:00', '17:00'),
    (2, 2, '09:00', '17:00'),
    (2, 3, '09:00', '17:00'),
    (2, 4, '09:00', '17:00'),
    (2, 5, '09:00', '17:00');

-- Modificar la tabla de usuarios para soportar más roles
ALTER TABLE users
  ALTER COLUMN role TYPE VARCHAR(50) CHECK (role IN ('admin', 'veterinarian', 'receptionist', 'assistant', 'client'));

-- Agregar tabla para configuración de horarios (más detallada que veterinarian_availability)
CREATE TABLE IF NOT EXISTS staff_schedules (
    id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_start TIME,
    break_end TIME,
    max_appointments INTEGER DEFAULT 8,
    appointment_duration INTEGER DEFAULT 30,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(staff_id, day_of_week)
);

-- Agregar tabla para administración de clínica
CREATE TABLE IF NOT EXISTS clinic_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuraciones iniciales
INSERT INTO clinic_settings (setting_name, setting_value, setting_type) VALUES
('clinic_name', 'Clínica Veterinaria', 'text'),
('business_hours_start', '09:00', 'time'),
('business_hours_end', '18:00', 'time'),
('appointment_duration', '30', 'integer'),
('max_appointments_per_day', '20', 'integer');

-- Crear un usuario administrador por defecto
INSERT INTO users (email, password, first_name, last_name, phone, role, is_active) VALUES
('admin@veterinary.com', '$2b$12$1s/qCzKhHguJW.CQYyyJzugL0YROHjD97Ot0v63YJuIF2fQrSWmPG', 'Admin', 'Sistema', '555-ADMIN', 'admin', TRUE)
ON CONFLICT (email) DO NOTHING;