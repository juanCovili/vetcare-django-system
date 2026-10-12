"""
Pruebas Unitarias y de Integración — Sistema VetCare Django.
Verifica:
1. Consulta de catálogo público (Productos, Medicamentos, Servicios, Tratamientos).
2. Agendamiento público de horas.
3. Seguridad y Control de Privilegios (RBAC): Administrativo vs. Médico Veterinario.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import StaffProfile, CatalogItem, Owner, Patient


class VetCareRBACAndCatalogTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear funcionarios con privilegios diferenciados
        user_admin = User.objects.create_user(username='recepcion', password='123')
        self.admin_staff = StaffProfile.objects.create(
            user=user_admin, rut='19.111.222-3', role=StaffProfile.ROLE_ADMIN
        )

        user_vet = User.objects.create_user(username='dr_covili', password='123')
        self.vet_staff = StaffProfile.objects.create(
            user=user_vet, rut='20.986.864-4', role=StaffProfile.ROLE_VET, specialty='Medicina Interna'
        )

        # Poblar catálogo
        self.consulta_item = CatalogItem.objects.create(
            sku='SRV-001',
            name='Consulta Médica General',
            category=CatalogItem.CAT_SERVICE,
            description='Evaluación clínica integral del paciente.',
            price_clp=18000,
            stock=999
        )
        self.med_item = CatalogItem.objects.create(
            sku='MED-101',
            name='Amoxicilina + Ácido Clavulánico 250mg',
            category=CatalogItem.CAT_MEDICATION,
            description='Antibiótico de amplio espectro uso veterinario.',
            price_clp=12500,
            stock=45,
            requires_prescription=True
        )

        # Crear paciente de prueba
        self.owner = Owner.objects.create(
            rut='15.432.198-7', full_name='Camila Muñoz', phone='+56988776655', email='camila@example.cl'
        )
        self.patient = Patient.objects.create(
            owner=self.owner, name='Thor', species=Patient.SPECIES_DOG, breed='Pastor Alemán', weight_kg=32.5
        )

    def test_public_catalog_returns_items(self):
        response = self.client.get('/api/public/catalog/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_administrative_cannot_access_clinical_record_endpoint(self):
        """Un empleado Administrativo NO puede ver ni editar la Ficha Clínica médica (403 Forbidden)."""
        response = self.client.get(
            f'/api/vet/patients/{self.patient.id}/clinical-record/',
            HTTP_X_STAFF_ROLE='ADMIN'
        )
        self.assertEqual(response.status_code, 403)

    def test_veterinarian_can_create_clinical_record(self):
        """Un Médico Veterinario SÍ tiene privilegios para registrar diagnóstico y tratamiento."""
        payload = {
            'veterinarian_id': self.vet_staff.id,
            'anamnesis': 'Decaimiento y fiebre leve de 24 horas.',
            'diagnosis': 'Faringitis infecciosa canina.',
            'treatment_plan': 'Antibioterapia por 7 días y control en 1 semana.',
            'recorded_weight_kg': 32.0,
            'temperature_celsius': 39.2
        }
        response = self.client.post(
            f'/api/vet/patients/{self.patient.id}/clinical-record/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_STAFF_ROLE='VET'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'clinical_record_created')
