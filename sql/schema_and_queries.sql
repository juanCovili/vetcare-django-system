-- ============================================================================
-- Esquema Relacional SQL & Consultas Analíticas — VetCare Clínica Veterinaria
-- Motor Compatible: PostgreSQL / SQLite3
-- ============================================================================

CREATE TABLE IF NOT EXISTS clinic_staffprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rut VARCHAR(15) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('ADMIN', 'VET')),
    specialty VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS clinic_catalogitem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('PRODUCTO', 'MEDICAMENTO', 'SERVICIO', 'TRATAMIENTO')),
    description TEXT NOT NULL,
    price_clp INTEGER NOT NULL CHECK (price_clp >= 0),
    stock INTEGER NOT NULL DEFAULT 0,
    requires_prescription BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clinic_owner (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rut VARCHAR(15) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(25) NOT NULL,
    email VARCHAR(254) NOT NULL
);

CREATE TABLE IF NOT EXISTS clinic_patient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES clinic_owner(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    species VARCHAR(20) NOT NULL,
    breed VARCHAR(100) NOT NULL,
    weight_kg NUMERIC(5,2) NOT NULL,
    allergies TEXT
);

CREATE TABLE IF NOT EXISTS clinic_appointment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES clinic_patient(id) ON DELETE CASCADE,
    veterinarian_id INTEGER REFERENCES clinic_staffprofile(id) ON DELETE SET NULL,
    service_id INTEGER NOT NULL REFERENCES clinic_catalogitem(id) ON DELETE RESTRICT,
    scheduled_at DATETIME NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
);

CREATE TABLE IF NOT EXISTS clinic_medicalrecord (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES clinic_patient(id) ON DELETE CASCADE,
    appointment_id INTEGER UNIQUE REFERENCES clinic_appointment(id) ON DELETE SET NULL,
    veterinarian_id INTEGER NOT NULL REFERENCES clinic_staffprofile(id) ON DELETE RESTRICT,
    anamnesis TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment_plan TEXT NOT NULL,
    recorded_weight_kg NUMERIC(5,2) NOT NULL,
    temperature_celsius NUMERIC(4,1) NOT NULL DEFAULT 38.5,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Consultas SQL de Reportabilidad Clínica y Comercial
-- ============================================================================

-- 1. Resumen de atenciones e ingresos estimados por categoría de servicio/tratamiento
SELECT
    c.category AS categoria,
    COUNT(a.id) AS total_citas,
    SUM(c.price_clp) AS ingresos_proyectados_clp
FROM clinic_appointment a
INNER JOIN clinic_catalogitem c ON a.service_id = c.id
WHERE a.status IN ('CONFIRMADA', 'COMPLETADA')
GROUP BY c.category
ORDER BY ingresos_proyectados_clp DESC;

-- 2. Historial clínico completo de pacientes con nombre del Médico Veterinario tratante
SELECT
    p.name AS paciente,
    p.species AS especie,
    o.full_name AS tutor,
    s.full_name AS medico_veterinario,
    m.diagnosis AS diagnostico,
    m.treatment_plan AS tratamiento,
    m.created_at AS fecha_atencion
FROM clinic_medicalrecord m
INNER JOIN clinic_patient p ON m.patient_id = p.id
INNER JOIN clinic_owner o ON p.owner_id = o.id
INNER JOIN clinic_staffprofile s ON m.veterinarian_id = s.id
ORDER BY m.created_at DESC;
