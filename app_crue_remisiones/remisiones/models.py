from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UsuarioCrue(AbstractUser):
    """Modelo de usuario unificado que reemplaza User + PerfilUsuario."""

    ROL_CHOICES = [
        ('DIRECTOR', 'Director'),
        ('RADIOOPERADOR', 'Radiooperador'),
    ]

    rol = models.CharField(
        max_length=15,
        choices=ROL_CHOICES,
        default='RADIOOPERADOR',
        verbose_name='Rol',
    )

    class Meta:
        verbose_name = 'Usuario CRUE'
        verbose_name_plural = 'Usuarios CRUE'

    def __str__(self):
        return f'{self.username} ({self.rol})'


class Remision(models.Model):
    """Registro de remisión de un paciente comentado por CRUE, ESE, SAS o EPS."""

    TIPO_DOC_CHOICES = [
        ('CC', 'CC'),
        ('TI', 'TI'),
        ('CE', 'CE'),
        ('RC', 'RC'),
        ('CN', 'CN'),
        ('OTRO', 'OTRO'),
    ]
    SEXO_CHOICES = [
        ('M', 'M'),
        ('F', 'F'),
    ]
    GEST_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
    ]
    ACEPTADO_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
        ('URG VITAL', 'URG VITAL'),
    ]

    # --- Identificación y tiempo de ingreso ---
    fecha = models.DateTimeField(
        verbose_name='Fecha y hora de ingreso',
        help_text='DD/MM/YYYY HH:MM',
    )

    # --- Identificación del paciente ---
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del paciente',
    )
    tipo_doc = models.CharField(
        max_length=5,
        choices=TIPO_DOC_CHOICES,
        default='CC',
        verbose_name='Tipo de documento',
    )
    doc = models.CharField(
        max_length=20,
        verbose_name='Número de documento',
    )

    gest = models.CharField(
        max_length=2,
        choices=GEST_CHOICES,
        default='NO',
        verbose_name='Gestante',
    )

    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        default='M',
        verbose_name='Sexo',
    )

    ESPECIALIDAD_CHOICES = [
        ('CIRUGIA DE COLUMNA', 'Cirugía de Columna'),
        ('CIRUGIA GENERAL', 'Cirugía General'),
        ('CIRUGIA PLASTICA', 'Cirugía Plástica'),
        ('CIRUGIA DEL TORAX', 'Cirugía del Tórax'),
        ('CIRUGIA MAXILOFACIAL', 'Cirugía Maxilofacial'),
        ('CIRUGIA VASCULAR', 'Cirugía Vascular'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('ENDOCRINOLOGIA', 'Endocrinología'),
        ('EPILEPTOLOGIA', 'Epileptología'),
        ('GENETICA HUMANA', 'Genética Humana'),
        ('GINECOLOGIA', 'Ginecología'),
        ('HEMATOLOGIA', 'Hematología'),
        ('INFECTOLOGIA', 'Infectología'),
        ('MEDICINA INTERNA', 'Medicina Interna'),
        ('NEFROLOGIA', 'Nefrología'),
        ('NEFROLOGIA PEDIATRICA', 'Nefrología Pediátrica'),
        ('NEUROCIRUGIA', 'Neurocirugía'),
        ('NEUROLOGIA', 'Neurología'),
        ('NEUROLOGIA PEDIATRICA', 'Neurología Pediátrica'),
        ('NUTRICION CLINICA', 'Nutrición Clínica'),
        ('OCULOPLASTIA', 'Oculoplastia'),
        ('OFTALMOLOGIA', 'Oftalmología'),
        ('ORTOPEDIA', 'Ortopedia'),
        ('OTORRINOLARINGOLOGIA', 'Otorrinolaringología'),
        ('PEDIATRIA', 'Pediatría'),
        ('PERINATOLOGIA', 'Perinatología'),
        ('REUMATOLOGIA', 'Reumatología'),
        ('TOXICOLOGIA CLINICA', 'Toxicología Clínica'),
        ('OTRA', 'Otra'),
    ]

    especialidad = models.CharField(
        max_length=50,
        choices=ESPECIALIDAD_CHOICES,
        blank=True,
        default='',
        verbose_name='Especialidad',
        help_text='Especialidad requerida por el paciente',
    )

    edad = models.CharField(
        max_length=20,
        verbose_name='Edad',
        help_text='Ej: 25 AÑOS, 3 MESES, 10 DIAS',
    )

    ESPECIALIDAD_CHOICES = [
        ('CIRUGIA DE COLUMNA', 'Cirugía de Columna'),
        ('CIRUGIA GENERAL', 'Cirugía General'),
        ('CIRUGIA PLASTICA', 'Cirugía Plástica'),
        ('CIRUGIA DEL TORAX', 'Cirugía del Tórax'),
        ('CIRUGIA MAXILOFACIAL', 'Cirugía Maxilofacial'),
        ('CIRUGIA VASCULAR', 'Cirugía Vascular'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('ENDOCRINOLOGIA', 'Endocrinología'),
        ('EPILEPTOLOGIA', 'Epileptología'),
        ('GENETICA HUMANA', 'Genética Humana'),
        ('GINECOLOGIA', 'Ginecología'),
        ('HEMATOLOGIA', 'Hematología'),
        ('INFECTOLOGIA', 'Infectología'),
        ('MEDICINA INTERNA', 'Medicina Interna'),
        ('NEFROLOGIA', 'Nefrología'),
        ('NEFROLOGIA PEDIATRICA', 'Nefrología Pediátrica'),
        ('NEUROCIRUGIA', 'Neurocirugía'),
        ('NEUROLOGIA', 'Neurología'),
        ('NEUROLOGIA PEDIATRICA', 'Neurología Pediátrica'),
        ('NUTRICION CLINICA', 'Nutrición Clínica'),
        ('OCULOPLASTIA', 'Oculoplastia'),
        ('OFTALMOLOGIA', 'Oftalmología'),
        ('ORTOPEDIA', 'Ortopedia'),
        ('OTORRINOLARINGOLOGIA', 'Otorrinolaringología'),
        ('PEDIATRIA', 'Pediatría'),
        ('PERINATOLOGIA', 'Perinatología'),
        ('REUMATOLOGIA', 'Reumatología'),
        ('TOXICOLOGIA CLINICA', 'Toxicología Clínica'),
        ('OTRA', 'Otra'),
    ]

    especialidad = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Especialidad',
        help_text='Especialidad requerida por el paciente',
    )

    # --- Información clínica ---
    diagnostico = models.TextField(
        blank=True,
        default='',
        verbose_name='Diagnóstico',
    )
    ta = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Tensión Arterial',
        help_text='Ej: 120/80 o NO REFIERE',
    )
    fc = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Frecuencia Cardíaca',
        help_text='Valor numérico o NO REFIERE',
    )
    fr = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Frecuencia Respiratoria',
        help_text='Valor numérico o NO REFIERE',
    )
    tm = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='Temperatura',
        help_text='Ej: 36° o NO REFIERE',
    )
    spo2 = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='Saturación O2',
        help_text='Ej: 98% o NO REFIERE',
    )
    glasg = models.CharField(
        max_length=10,
        blank=True,
        default='15/15',
        verbose_name='Glasgow',
        help_text='Ej: 15/15 o NO REFIERE',
    )

    # --- Información institucional ---
    eps = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='EPS',
    )
    institucion_reporta = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Institución que reporta',
    )
    municipio = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Municipio',
    )
    medico_refiere = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Médico que refiere',
    )
    medico_hudn = models.TextField(
        blank=True,
        default='',
        verbose_name='Médico HUDN que confirma',
    )
    radio_operador = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Radio operador',
    )
    observacion = models.TextField(
        blank=True,
        default='',
        verbose_name='Observación',
    )

    # --- Resultado ---
    aceptado = models.CharField(
        max_length=10,
        choices=ACEPTADO_CHOICES,
        default='NO',
        verbose_name='Aceptado',
    )
    fecha_res = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha y hora de respuesta',
        help_text='DD/MM/YYYY HH:MM',
    )
    # OPORTUNIDAD: NO se almacena. Se calcula dinámicamente como fecha_res - fecha.

    # --- Auditoría ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado en')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado en')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remisiones_creadas',
        verbose_name='Creado por',
    )

    class Meta:
        ordering = ['fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['doc']),
        ]
        verbose_name = 'Remisión'
        verbose_name_plural = 'Remisiones'

    def __str__(self):
        return f'{self.fecha} - {self.nombre} ({self.doc})'

    @property
    def es_editable(self) -> bool:
        """
        Un registro es editable si su fecha.date() es igual a la fecha de hoy
        en la zona horaria local configurada en Django.
        Los registros históricos (fecha.date() < hoy) son de solo lectura.
        """
        return self.fecha.astimezone(timezone.get_current_timezone()).date() == timezone.localdate()
