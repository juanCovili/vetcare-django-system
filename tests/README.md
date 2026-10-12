# 🧪 Suite de Pruebas Automatizadas (`Django TestCase`)

Este directorio contiene las pruebas automatizadas del sistema **VetCare Clínico & Comercial**, organizadas en dos módulos de verificación:

1. **[`test_models_and_integrity.py`](./test_models_and_integrity.py):**
   - Detección automática de alertas de stock crítico (`stock < min_stock`) en medicamentos e insumos.
   - Regla de negocio anti-colisión de agenda (`clean()`): impide que dos pacientes reserven la misma fecha y hora con el mismo médico veterinario.
   - Integridad referencial `ON DELETE PROTECT`: garantiza que ningún registro de paciente pueda eliminarse si tiene fichas clínicas asociadas.
2. **[`test_rbac_permissions.py`](./test_rbac_permissions.py):**
   - Acceso público (`HTTP 200`) al catálogo de productos, medicamentos y servicios sin necesidad de autenticación.
   - Bloqueo de seguridad (`HTTP 403 Forbidden`) cuando un usuario con rol **Administrativo (`ADMIN`)** intenta crear o modificar una **Ficha Clínica Médica**.
   - Autorización exitosa (`HTTP 201 Created`) cuando un usuario con rol **Médico Veterinario (`VET`)** registra diagnósticos y tratamientos en la ficha del paciente.

---

## ▶️ Cómo Ejecutar las Pruebas

```bash
python manage.py test tests
```
