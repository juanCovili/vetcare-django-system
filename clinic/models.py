"""
Modelos Relacionales ORM (Patrón MVT) — Sistema Clínico y Comercial Veterinario VetCare.

Incluye:
1. Control de Acceso Basado en Roles (RBAC): Administrativo vs. Médico Veterinario.
2. Catálogo Público: Productos, Medicamentos, Servicios y Tratamientos.
3. Gestión de Pacientes (Mascotas) y Tutores (Clientes).
4. Agendamiento de Horas Médicas (Público y Recepción Administrativa).
5. Ficha Clínica Electrónica e Historial de Tratamientos (Exclusivo Médico Veterinario).
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class StaffProfile(models.Model):
    """Perfil de empleado con privilegios diferenciados (RBAC)."""
    ROLE_ADMIN = 'ADMIN'
    ROLE_VET = 'VET'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrativo / Recepción'),
        (ROLE_VET, 'Médico Veterinario'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    rut = models.CharField(max_length=15, unique=True, help_text="RUT chileno del funcionario (ej. 18.456.789-K)")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_ADMIN)
    specialty = models.CharField(max_length=100, blank=True, help_text="Especialidad clínica (solo Veterinarios)")
    phone = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil de Funcionario'
        verbose_name_plural = 'Perfiles de Funcionarios'

    def is_veterinarian(self) -> bool:
        return self.role == self.ROLE_VET

    def is_administrative(self) -> bool:
        return self.role == self.ROLE_ADMIN

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class CatalogItem(models.Model):
    """Catálogo público de Productos, Medicamentos, Servicios y Tratamientos."""
    CAT_PRODUCT = 'PRODUCTO'
    CAT_MEDICATION = 'MEDICAMENTO'
    CAT_SERVICE = 'SERVICIO'
    CAT_TREATMENT = 'TRATAMIENTO'

    CATEGORY_CHOICES = [
        (CAT_PRODUCT, 'Producto / Alimento / Accesorio'),
        (CAT_MEDICATION, 'Medicamento / Farmacia Veterinaria'),
        (CAT_SERVICE, 'Servicio Clínico / Consulta'),
        (CAT_TREATMENT, 'Tratamiento / Procedimiento'),
    ]

    sku = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price_clp = models.PositiveIntegerField(validators=[MinValueValidator(0)], help_text="Precio en pesos chilenos (CLP)")
    stock = models.PositiveIntegerField(default=0, help_text="Stock físico disponible en bodega/farmacia")
    requires_prescription = models.BooleanField(default=False, help_text="Indica si requiere receta médico-veterinaria")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Ítem de Catálogo'
        verbose_name_plural = 'Catálogo de Productos y Servicios'

    def __str__(self):
        return f"[{self.sku}] {self.name} (${self.price_clp:,} CLP)"


class Owner(models.Model):
    """Tutor / Dueño responsable de la mascota."""
    rut = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    address = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} (RUT: {self.rut})"


class Patient(models.Model):
    """Ficha maestra del Paciente (Mascota)."""
    SPECIES_DOG = 'CANINO'
    SPECIES_CAT = 'FELINO'
    SPECIES_EXOTIC = 'EXOTICO'

    SPECIES_CHOICES = [
        (SPECIES_DOG, 'Canino (Perro)'),
        (SPECIES_CAT, 'Felino (Gato)'),
        (SPECIES_EXOTIC, 'Exótico / Otro'),
    ]

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='patients')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, default=SPECIES_DOG)
    breed = models.CharField(max_length=100, default='Mestizo')
    birth_date = models.DateField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.1)])
    allergies = models.TextField(blank=True, help_text="Alergias medicamentosas o alimentarias conocidas")
    microchip_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_species_display()} - Tutor: {self.owner.full_name})"


class Appointment(models.Model):
    """Agendamiento de Horas Médicas (creado desde Portal Público o por Administrativo)."""
    STATUS_PENDING = 'PENDIENTE'
    STATUS_CONFIRMED = 'CONFIRMADA'
    STATUS_IN_PROGRESS = 'EN_ATENCION'
    STATUS_COMPLETED = 'COMPLETADA'
    STATUS_CANCELLED = 'CANCELADA'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente de Confirmación'),
        (STATUS_CONFIRMED, 'Confirmada por Recepción'),
        (STATUS_IN_PROGRESS, 'En Box de Atención'),
        (STATUS_COMPLETED, 'Atención Finalizada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    veterinarian = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': StaffProfile.ROLE_VET},
        related_name='assigned_appointments'
    )
    service = models.ForeignKey(CatalogItem, on_delete=models.PROTECT, related_name='appointments')
    scheduled_at = models.DateTimeField()
    reason = models.CharField(max_length=255, help_text="Motivo de consulta ingresado al agendar")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reception_notes = models.TextField(blank=True, help_text="Notas ingresadas por personal Administrativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.scheduled_at:%Y-%m-%d %H:%M} - {self.patient.name} ({self.get_status_display()})"


class MedicalRecord(models.Model):
    """
    Registro Clínico en la Ficha del Paciente.
    PRIVILEGIO: Solo puede ser creado/editado por personal con rol Médico Veterinario (VET).
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='clinical_record')
    veterinarian = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        limit_choices_to={'role': StaffProfile.ROLE_VET},
        related_name='authored_records'
    )
    anamnesis = models.TextField(help_text="Historia clínica y síntomas relatados")
    diagnosis = models.TextField(help_text="Diagnóstico clínico presuntivo o definitivo")
    treatment_plan = models.TextField(help_text="Procedimiento y tratamiento médico indicado")
    prescribed_medications = models.ManyToManyField(
        CatalogItem,
        blank=True,
        limit_choices_to={'category': CatalogItem.CAT_MEDICATION},
        related_name='prescriptions'
    )
    recorded_weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    temperature_celsius = models.DecimalField(max_digits=4, decimal_places=1, default=38.5)
    next_checkup_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ficha / Evolución Clínica'
        verbose_name_plural = 'Fichas y Evoluciones Clínicas'

    def __str__(self):
        return f"Ficha #{self.id} - {self.patient.name} ({self.created_at:%Y-%m-%d})"
