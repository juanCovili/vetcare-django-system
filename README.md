# 🐾 VetCare — Sistema de Gestión Clínica y Comercial Veterinaria (Django MVT + RBAC)

Aplicación web full-stack desarrollada en **Python y Django** bajo el patrón arquitectónico **MVT (Model-View-Template)** con base de datos relacional **SQLite / PostgreSQL** y **Control de Acceso Basado en Roles (RBAC)**.

El sistema separa de forma estricta la experiencia del **Portal Público para Clientes** y la **Intranet Privada de Funcionarios** según sus privilegios (`Administrativo` vs. `Médico Veterinario`).

---

## 🏗️ Arquitectura del Sistema

1. **Portal Público (Clientes y Tutores):**
   - **Catálogo Digital Filtrable:** Visualización de **Productos**, **Medicamentos** (indicando si requieren receta retenida), **Servicios Clínicos** y **Tratamientos** con precios en CLP y disponibilidad de stock en tiempo real.
   - **Agendamiento de Hora Médica Online:** Formulario conectado al modelo relacional que registra al Tutor (`Owner`), la Mascota (`Patient`) y bloquea la solicitud de hora médica (`Appointment`).

2. **Intranet Privada con Control de Privilegios (RBAC):**
   - **Rol Administrativo (`ADMIN`):**
     - Acceso al panel de recepción de horas agendadas (confirmación, reprogramación, cambio de estado a *En Box* y notas de admisión).
     - Control de stock de farmacia y productos.
     - *Restricción de seguridad:* No posee acceso de escritura ni lectura sensible sobre diagnósticos médicos (`HTTP 403 Forbidden`).
   - **Rol Médico Veterinario (`VET`):**
     - Acceso exclusivo a la **Ficha Clínica del Paciente (`MedicalRecord`)**.
     - Registro de anamnesis, control de signos vitales (peso, temperatura), diagnóstico clínico, plan de tratamiento y prescripción de medicamentos.

---

## 📂 Estructura del Proyecto

```text
vetcare-django-system/
├── manage.py                      # Utilidad CLI de administración Django
├── requirements.txt               # Dependencias (Django, Gunicorn, Pytest)
├── vetcare/                       # Configuración del proyecto principal
│   ├── settings.py                # Configuración ORM, localización es-CL y seguridad
│   └── urls.py                    # Enrutador raíz
├── clinic/                        # Aplicación principal (Patrón MVT)
│   ├── models.py                  # Modelos: StaffProfile, CatalogItem, Owner, Patient, Appointment, MedicalRecord
│   ├── views.py                   # Controladores públicos, Intranet RBAC (@role_required) y API JSON
│   ├── urls.py                    # Endpoints públicos, administrativos y clínicos
│   └── tests.py                   # Pruebas automatizadas de catálogo y seguridad de roles (403 vs 201)
├── sql/
│   └── schema_and_queries.sql     # DDL relacional y consultas SQL de gestión clínica
└── docs/
    └── index.html                 # Demo interactiva (Portal Público + Intranet Administrativo/Veterinario)
```

---

## 🚀 Ejecución Local

```bash
# 1. Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Aplicar migraciones a la base de datos SQLite
python manage.py makemigrations clinic
python manage.py migrate

# 3. Ejecutar suite de pruebas unitarias y de permisos RBAC
python manage.py test clinic

# 4. Iniciar servidor de desarrollo
python manage.py runserver
```

---

## Autor

**Juan Andrés Covili Cabezas**  
Ingeniero en Informática / Analista Programador — INACAP
