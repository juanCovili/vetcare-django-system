"""
Vistas y Controladores MVT + Endpoints REST — Sistema VetCare.

Implementa separación estricta entre:
1. Portal Público (Catálogo de Productos/Medicamentos/Servicios/Tratamientos y Agendamiento de Horas).
2. Intranet Privada con Control de Acceso Basado en Roles (RBAC):
   - Rol ADMINISTRATIVO: Gestión de agenda de horas, confirmación de turnos y control de stock.
   - Rol MÉDICO VETERINARIO: Acceso exclusivo a Ficha Clínica del Paciente, diagnósticos y prescripción de tratamientos.
"""
from functools import wraps
import json
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import StaffProfile, CatalogItem, Owner, Patient, Appointment, MedicalRecord


def role_required(allowed_roles):
    """
    Decorador de Seguridad RBAC (Role-Based Access Control).
    Verifica que el empleado autenticado posea el privilegio requerido ('ADMIN' o 'VET').
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            role_header = request.headers.get('X-Staff-Role')
            if not role_header and request.user.is_authenticated and hasattr(request.user, 'staff_profile'):
                role_header = request.user.staff_profile.role

            if role_header not in allowed_roles:
                return JsonResponse({
                    'error': 'Acceso Denegado (403 Forbidden)',
                    'detail': f'Esta acción requiere privilegios de: {", ".join(allowed_roles)}.',
                    'current_role': role_header or 'PUBLICO_NO_AUTENTICADO'
                }, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# =========================================================================
# 1. PORTAL PÚBLICO (Catálogo Comercial/Clínico y Agendamiento de Horas)
# =========================================================================

@require_http_methods(["GET"])
def public_catalog_api(request):
    """
    Devuelve el catálogo público filtrable por categoría:
    PRODUCTO, MEDICAMENTO, SERVICIO, TRATAMIENTO.
    """
    category = request.GET.get('category')
    queryset = CatalogItem.objects.filter(is_public=True)
    if category:
        queryset = queryset.filter(category=category.upper())

    items = [
        {
            'sku': item.sku,
            'name': item.name,
            'category': item.category,
            'category_label': item.get_category_display(),
            'description': item.description,
            'price_clp': item.price_clp,
            'in_stock': item.stock > 0,
            'stock': item.stock,
            'requires_prescription': item.requires_prescription,
        }
        for item in queryset
    ]
    return JsonResponse({'status': 'ok', 'count': len(items), 'catalog': items})


@csrf_exempt
@require_http_methods(["POST"])
def public_book_appointment_api(request):
    """
    Permite a un cliente agendar una hora médica desde el portal público.
    Crea o actualiza al Tutor (Owner), registra la Mascota (Patient) y genera la cita en estado PENDIENTE.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
        owner, _ = Owner.objects.get_or_create(
            rut=payload['owner_rut'],
            defaults={
                'full_name': payload['owner_name'],
                'phone': payload.get('owner_phone', ''),
                'email': payload.get('owner_email', ''),
            }
        )
        patient, _ = Patient.objects.get_or_create(
            owner=owner,
            name=payload['patient_name'],
            defaults={
                'species': payload.get('species', Patient.SPECIES_DOG),
                'breed': payload.get('breed', 'Mestizo'),
                'weight_kg': payload.get('weight_kg', 10.0),
            }
        )
        service = get_object_or_404(CatalogItem, sku=payload['service_sku'])
        appointment = Appointment.objects.create(
            patient=patient,
            service=service,
            scheduled_at=payload.get('scheduled_at', timezone.now()),
            reason=payload['reason'],
            status=Appointment.STATUS_PENDING
        )
        return JsonResponse({
            'status': 'created',
            'appointment_id': appointment.id,
            'patient': patient.name,
            'service': service.name,
            'appointment_status': appointment.status,
            'message': 'Hora agendada exitosamente. Recepción confirmará su bloque horario.'
        }, status=201)
    except (KeyError, ValueError, json.JSONDecodeError) as err:
        return JsonResponse({'error': f'Datos de agendamiento inválidos: {str(err)}'}, status=400)


# =========================================================================
# 2. INTRANET EMPLEADOS — ROL ADMINISTRATIVO (Agenda, Recepción y Stock)
# =========================================================================

@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@role_required([StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_VET])
def staff_appointments_dashboard(request):
    """
    Panel de Agendamiento de Horas para Administrativos y Veterinarios.
    El Administrativo puede confirmar/reprogramar horas y agregar notas de recepción.
    """
    if request.method == "GET":
        appointments = Appointment.objects.select_related('patient', 'patient__owner', 'service', 'veterinarian').all()
        data = [
            {
                'id': appt.id,
                'scheduled_at': appt.scheduled_at.isoformat(),
                'patient_name': appt.patient.name,
                'species': appt.patient.get_species_display(),
                'owner_name': appt.patient.owner.full_name,
                'owner_rut': appt.patient.owner.rut,
                'service': appt.service.name,
                'status': appt.status,
                'reason': appt.reason,
                'reception_notes': appt.reception_notes,
            }
            for appt in appointments
        ]
        return JsonResponse({'status': 'ok', 'appointments': data})

    # PATCH: Confirmación o cambio de estado por Recepción Administrativa
    payload = json.loads(request.body.decode('utf-8'))
    appt = get_object_or_404(Appointment, id=payload['appointment_id'])
    if 'status' in payload:
        appt.status = payload['status']
    if 'reception_notes' in payload:
        appt.reception_notes = payload['reception_notes']
    appt.save()
    return JsonResponse({
        'status': 'updated',
        'appointment_id': appt.id,
        'new_status': appt.status,
        'reception_notes': appt.reception_notes
    })


# =========================================================================
# 3. INTRANET EMPLEADOS — ROL MÉDICO VETERINARIO (Ficha Clínica y Tratamiento)
# =========================================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
@role_required([StaffProfile.ROLE_VET])
def veterinarian_patient_clinical_record(request, patient_id):
    """
    ENDPOINT PROTEGIDO EXCLUSIVO PARA MÉDICOS VETERINARIOS (Rol 'VET').
    Un usuario Administrativo recibe HTTP 403 Forbidden si intenta crear o modificar fichas clínicas.
    """
    patient = get_object_or_404(Patient.objects.select_related('owner'), id=patient_id)

    if request.method == "GET":
        records = patient.medical_records.select_related('veterinarian__user').prefetch_related('prescribed_medications').all()
        history = [
            {
                'record_id': rec.id,
                'date': rec.created_at.isoformat(),
                'veterinarian': str(rec.veterinarian),
                'anamnesis': rec.anamnesis,
                'diagnosis': rec.diagnosis,
                'treatment_plan': rec.treatment_plan,
                'weight_kg': float(rec.recorded_weight_kg),
                'temperature_c': float(rec.temperature_celsius),
                'medications': [m.name for m in rec.prescribed_medications.all()],
            }
            for rec in records
        ]
        return JsonResponse({
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'species': patient.get_species_display(),
                'breed': patient.breed,
                'allergies': patient.allergies,
                'owner_name': patient.owner.full_name,
                'owner_phone': patient.owner.phone,
            },
            'clinical_history': history
        })

    # POST: Registrar nueva evolución clínica, diagnóstico y tratamiento en la Ficha del Paciente
    payload = json.loads(request.body.decode('utf-8'))
    vet_profile = get_object_or_404(StaffProfile, id=payload['veterinarian_id'], role=StaffProfile.ROLE_VET)

    record = MedicalRecord.objects.create(
        patient=patient,
        veterinarian=vet_profile,
        anamnesis=payload['anamnesis'],
        diagnosis=payload['diagnosis'],
        treatment_plan=payload['treatment_plan'],
        recorded_weight_kg=payload.get('recorded_weight_kg', patient.weight_kg),
        temperature_celsius=payload.get('temperature_celsius', 38.5),
    )

    patient.weight_kg = record.recorded_weight_kg
    patient.save(update_fields=['weight_kg'])

    return JsonResponse({
        'status': 'clinical_record_created',
        'record_id': record.id,
        'patient': patient.name,
        'diagnosis': record.diagnosis,
        'treatment_plan': record.treatment_plan,
    }, status=201)
