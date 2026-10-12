from django.contrib.auth.models import User
from django.test import TestCase, Client
from clinic.models import StaffProfile, Owner, Patient


class VetCareRBACSecurityTests(TestCase):
    """
    Pruebas de Seguridad y Control de Acceso Basado en Roles (RBAC):
    1. Portal Público accesible para clientes sin sesión.
    2. Rol ADMINISTRATIVO autorizado para gestionar agenda/stock pero BLOQUEADO (HTTP 403) en Ficha Clínica.
    3. Rol MEDICO VETERINARIO autorizado para crear y editar Fichas Clínicas y Tratamientos.
    """

    def setUp(self):
        self.client = Client()

        # Usuario con rol Administrativo
        self.admin_user = User.objects.create_user(username="recepcion_admin", password="StrongPassword123!")
        StaffProfile.objects.create(user=self.admin_user, role="ADMIN", rut="18.111.222-3")

        # Usuario con rol Médico Veterinario
        self.vet_user = User.objects.create_user(username="dr_veterinario", password="StrongPassword123!")
        StaffProfile.objects.create(user=self.vet_user, role="VET", rut="16.444.555-6")

        self.owner = Owner.objects.create(
            rut="14.222.333-4",
            full_name="Carlos Fuentes",
            email="carlos@example.cl",
            phone="+56911223344",
        )
        self.patient = Patient.objects.create(
            name="Luna",
            species="FELINO",
            breed="Común Europeo",
            weight_kg=4.2,
            owner=self.owner,
        )

    def test_public_catalog_endpoint_accessible_without_login(self):
        """Cualquier visitante puede consultar el catálogo público de productos y servicios."""
        response = self.client.get("/api/catalogo/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_administrative_staff_cannot_create_clinical_record(self):
        """Un administrativo autenticado recibe HTTP 403 Forbidden si intenta emitir una ficha médica."""
        self.client.login(username="recepcion_admin", password="StrongPassword123!")
        response = self.client.post(
            "/intranet/ficha-clinica/crear/",
            data={
                "patient_id": self.patient.id,
                "diagnosis": "Intento no autorizado",
                "treatment_plan": "N/A",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_veterinarian_can_create_clinical_record(self):
        """Un Médico Veterinario autenticado puede emitir fichas clínicas y prescribir tratamientos."""
        self.client.login(username="dr_veterinario", password="StrongPassword123!")
        response = self.client.post(
            "/intranet/ficha-clinica/crear/",
            data={
                "patient_id": self.patient.id,
                "anamnesis": "Control sano anual",
                "diagnosis": "Paciente clínicamente sano",
                "treatment_plan": "Vacuna Triple Felina + Desparasitación interna",
                "temperature_c": "38.4",
            },
        )
        self.assertIn(response.status_code, (200, 201))
