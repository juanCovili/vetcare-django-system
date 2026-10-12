from datetime import date, time
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from clinic.models import CatalogItem, Owner, Patient, Appointment, ClinicalRecord


class VetCareRelationalIntegrityTests(TestCase):
    """
    Pruebas unitarias de integridad relacional SQL (3FN), reglas de negocio
    de inventario farmacéutico y prevención de solapamiento de citas médicas.
    """

    def setUp(self):
        self.owner = Owner.objects.create(
            rut="15.432.987-K",
            full_name="Camila Rojas",
            email="camila.rojas@example.cl",
            phone="+56987654321",
        )
        self.patient = Patient.objects.create(
            name="Thor",
            species="CANINO",
            breed="Pastor Alemán",
            birth_date=date(2022, 5, 10),
            weight_kg=32.5,
            owner=self.owner,
        )

    def test_critical_stock_alert_detection(self):
        """Verifica que el modelo detecte automáticamente medicamentos bajo el stock mínimo."""
        med_critico = CatalogItem.objects.create(
            sku="MED-AMOX-250",
            name="Amoxicilina + Ácido Clavulánico 250mg",
            category="MEDICAMENTO",
            price_clp=14900,
            stock=4,
            min_stock=15,
            requires_prescription=True,
        )
        med_optimo = CatalogItem.objects.create(
            sku="PROD-COLLAR-M",
            name="Collar Antiparasitario Mediano",
            category="PRODUCTO",
            price_clp=18500,
            stock=30,
            min_stock=10,
            requires_prescription=False,
        )
        self.assertTrue(med_critico.is_low_stock)
        self.assertFalse(med_optimo.is_low_stock)

    def test_prevent_double_booking_same_veterinarian(self):
        """Impide agendar dos horas médicas al mismo veterinario en la misma fecha y bloque horario."""
        Appointment.objects.create(
            patient=self.patient,
            veterinarian_name="Dra. Valentina Muñoz",
            appointment_date=date(2026, 11, 20),
            appointment_time=time(10, 30),
            reason="Control post-operatorio",
            status="CONFIRMADA",
        )
        duplicate_appt = Appointment(
            patient=self.patient,
            veterinarian_name="Dra. Valentina Muñoz",
            appointment_date=date(2026, 11, 20),
            appointment_time=time(10, 30),
            reason="Vacunación séxtuple",
            status="PENDIENTE",
        )
        with self.assertRaises(ValidationError):
            duplicate_appt.clean()

    def test_clinical_record_protects_patient_deletion(self):
        """
        Verifica la restricción SQL ON DELETE PROTECT: no se puede eliminar un paciente
        si posee fichas clínicas históricas registradas.
        """
        ClinicalRecord.objects.create(
            patient=self.patient,
            veterinarian_name="Dr. Matías Soto",
            anamnesis="Paciente ingresa por decaimiento y pérdida de apetito.",
            diagnosis="Gastroenteritis aguda leve",
            treatment_plan="Hidratación subcutánea + dieta blanda por 5 días",
            temperature_c=39.1,
        )
        with self.assertRaises(ProtectedError):
            self.patient.delete()
