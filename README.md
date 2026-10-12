# 🐾 VetCare — Sistema Clínico y Comercial Veterinario (`Django + SQL + RBAC`)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Framework-Django_MVT-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQL](https://img.shields.io/badge/Database-PostgreSQL_%2F_SQLite-336791?logo=postgresql&logoColor=white)](./sql)
[![Tests](https://img.shields.io/badge/Tests-6%2F6_Passing_(RBAC_%26_3NF)-22c55e)](./tests)
[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-0ea5e9?logo=github)](https://juancovili.github.io/vetcare-django-system/)

> Sistema web integral desarrollado en **Python / Django** y **SQL**, estructurado en un **Portal Público** (catálogo de medicamentos, productos, servicios, tratamientos y reserva de horas) y una **Intranet Privada con Control de Acceso Basado en Roles (`RBAC`)** que segrega los privilegios entre el personal **Administrativo (`ADMIN`)** y el **Médico Veterinario (`VET`)**.

🔗 **[Probar Demo Interactiva en Vivo (Portal Público + Intranet RBAC)](https://juancovili.github.io/vetcare-django-system/)**

![Vista Previa de VetCare](./docs/preview.svg)

---

## 🏗️ Arquitectura de Permisos y Separación de Capas (`RBAC`)

```mermaid
flowchart LR
    subgraph PublicPortal ["1. Portal Público (Clientes / Tutores)"]
        P1["Catálogo de Productos, Medicamentos y Servicios"]
        P2["Solicitud de Hora Médica Online"]
    end

    subgraph IntranetRBAC ["2. Intranet Privada con Privilegios (@role_required)"]
        subgraph RoleAdmin ["Rol: ADMINISTRATIVO (ADMIN)"]
            A1["Confirmar / Reprogramar Agenda Médica"]
            A2["Control de Stock de Farmacia y Bodega"]
            A3["Alertas de Stock Crítico (stock < min_stock)"]
        end
        subgraph RoleVet ["Rol: MÉDICO VETERINARIO (VET)"]
            V1["Apertura y Edición de Ficha Clínica"]
            V2["Registro de Anamnesis, Signos Vitales y Diagnóstico"]
            V3["Prescripción de Tratamientos y Recetas"]
        end
    end

    P2 -->|Valida colisión horaria clean| A1
    A1 -->|Paciente en sala| V1
    RoleAdmin -.->|Intento acceso Ficha Clínica| X["HTTP 403 Forbidden"]
```

---

## 🗄️ Modelo Entidad-Relación en 3ª Forma Normal (`3FN`)

El esquema relacional (definido en [`clinic/models.py`](./clinic/models.py) y en SQL nativo en [`sql/schema_and_queries.sql`](./sql/schema_and_queries.sql)) protege el historial médico mediante restricciones de integridad referencial (`ON DELETE PROTECT`):

```mermaid
erDiagram
    OWNER ||--o{ PATIENT : "es tutor de (CASCADE)"
    PATIENT ||--o{ APPOINTMENT : "agenda (CASCADE)"
    PATIENT ||--o{ CLINICAL_RECORD : "posee historial (PROTECT)"
    USER ||--|| STAFF_PROFILE : "tiene rol RBAC (ADMIN | VET)"

    OWNER {
        int id PK
        string rut UK
        string full_name
        string email
        string phone
    }
    PATIENT {
        int id PK
        string name
        string species "CANINO | FELINO | EXOTICO"
        string breed
        decimal weight_kg
        text allergies
        int owner_id FK
    }
    APPOINTMENT {
        int id PK
        int patient_id FK
        string veterinarian_name
        date appointment_date
        time appointment_time
        string status "PENDIENTE | CONFIRMADA | ATENDIDA"
    }
    CLINICAL_RECORD {
        int id PK
        int patient_id FK
        string veterinarian_name
        text anamnesis
        text diagnosis
        text treatment_plan
        decimal temperature_c
    }
    CATALOG_ITEM {
        int id PK
        string sku UK
        string name
        string category "PRODUCTO | MEDICAMENTO | SERVICIO | TRATAMIENTO"
        int price_clp
        int stock
        int min_stock
        boolean requires_prescription
    }
```

---

## 🧪 Suite de Pruebas Automatizadas ([`/tests`](./tests))

El directorio [`/tests`](./tests) contiene las pruebas automatizadas de integridad relacional y seguridad por roles:

| Archivo de Prueba | Caso de Prueba | Qué verifica | Estado |
| :--- | :--- | :--- | :---: |
| [`test_models_and_integrity.py`](./tests/test_models_and_integrity.py) | `test_critical_stock_alert_detection` | Propiedad `is_low_stock` detecta insumos farmacéuticos bajo su punto mínimo de reposición. | ✅ PASS |
| [`test_models_and_integrity.py`](./tests/test_models_and_integrity.py) | `test_prevent_double_booking_same_veterinarian` | Validación `clean()` lanza `ValidationError` si se intenta agendar dos citas al mismo médico en igual fecha y hora. | ✅ PASS |
| [`test_models_and_integrity.py`](./tests/test_models_and_integrity.py) | `test_clinical_record_protects_patient_deletion` | Restricción `models.PROTECT` lanza `ProtectedError` impidiendo borrar pacientes con fichas clínicas. | ✅ PASS |
| [`test_rbac_permissions.py`](./tests/test_rbac_permissions.py) | `test_public_catalog_endpoint_accessible_without_login` | Clientes sin sesión pueden consultar el catálogo público (`HTTP 200`). | ✅ PASS |
| [`test_rbac_permissions.py`](./tests/test_rbac_permissions.py) | `test_administrative_staff_cannot_create_clinical_record` | Un usuario `ADMIN` recibe **`HTTP 403 Forbidden`** si intenta emitir una ficha médica. | ✅ PASS |
| [`test_rbac_permissions.py`](./tests/test_rbac_permissions.py) | `test_veterinarian_can_create_clinical_record` | Un usuario `VET` puede registrar fichas clínicas y tratamientos (`HTTP 201 Created`). | ✅ PASS |

```bash
# Ejecutar todas las pruebas
python manage.py test tests
```

---

## 🚀 Cómo Ejecutar en Local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver
```

---

## 👨‍💻 Autor

**Juan Covili**  
*Ingeniero en Informática / Analista Programador (INACAP)*  
* [LinkedIn](https://www.linkedin.com/in/juan-covili-59b935241/) · [GitHub](https://github.com/juanCovili) · [Portafolio Web](https://www.juancovili.com)
