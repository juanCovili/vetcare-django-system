from django.urls import path
from . import views

urlpatterns = [
    # Rutas Públicas (Catálogo de Productos, Medicamentos, Servicios y Agendamiento de Hora)
    path('api/public/catalog/', views.public_catalog_api, name='public_catalog'),
    path('api/public/appointments/book/', views.public_book_appointment_api, name='public_book_appointment'),

    # Rutas Intranet Privada (Administrativo y Médico Veterinario)
    path('api/staff/appointments/', views.staff_appointments_dashboard, name='staff_appointments'),

    # Ruta Clínica Exclusiva Médico Veterinario (Ficha Paciente y Tratamientos)
    path('api/vet/patients/<int:patient_id>/clinical-record/', views.veterinarian_patient_clinical_record, name='vet_clinical_record'),
]
