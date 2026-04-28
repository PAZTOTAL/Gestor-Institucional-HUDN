from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


# ── Modelos para Gestión de Recargos / Turnos ────────────────────────────────

class AreaRecargos(models.Model):
    nombre      = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering     = ['nombre']
        verbose_name = 'Área (Recargos)'
        verbose_name_plural = 'Áreas (Recargos)'

    def __str__(self):
        return self.nombre


class TrabajadorRecargos(models.Model):
    TIPO_CHOICES = [
        ('permanente', 'Planta Permanente'),
        ('temporal',   'Planta Temporal'),
        ('ops',        'OPS'),
    ]
    nombre    = models.CharField(max_length=150)
    documento = models.CharField(max_length=20, unique=True)
    cargo     = models.CharField(max_length=100, blank=True, default='')
    area      = models.ForeignKey(AreaRecargos, on_delete=models.SET_NULL, null=True, blank=True, related_name='trabajadores')
    tipo      = models.CharField(max_length=15, choices=TIPO_CHOICES, default='permanente')

    class Meta:
        ordering     = ['nombre']
        verbose_name = 'Trabajador (Recargos)'
        verbose_name_plural = 'Trabajadores (Recargos)'

    def __str__(self):
        return f"{self.nombre} ({self.documento})"


class TurnoRecargos(models.Model):
    TURNO_CHOICES = [
        ('manana',       'Mañana (07:00–13:00)'),
        ('tarde',        'Tarde (13:00–19:00)'),
        ('noche',        'Noche (19:00–07:00)'),
        ('manana_noche', 'Mañana-Noche (07:00–13:00 / 19:00–07:00)'),
        ('manana_tarde', 'Mañana-Tarde (07:00–19:00)'),
        ('veinticuatro', '24 Horas (07:00–07:00)'),
        ('por_horas',    'Por horas'),
        ('libre',        'Libre'),
    ]
    empleado_id     = models.IntegerField(help_text='ID del empleado (SQL Server o local)')
    fecha           = models.DateField()
    turno           = models.CharField(max_length=15, choices=TURNO_CHOICES)
    observaciones   = models.CharField(max_length=500, blank=True, default='')
    horas_diurnas   = models.IntegerField(null=True, blank=True, default=None)
    horas_nocturnas = models.IntegerField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ['empleado_id', 'fecha']
        ordering        = ['fecha']
        verbose_name    = 'Turno (Recargos)'
        verbose_name_plural = 'Turnos (Recargos)'

    def __str__(self):
        return f"Emp {self.empleado_id} — {self.fecha} — {self.get_turno_display()}"


class ObservacionMensualRecargos(models.Model):
    empleado_id = models.IntegerField()
    year        = models.IntegerField()
    month       = models.IntegerField()
    observacion = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ['empleado_id', 'year', 'month']
        verbose_name    = 'Observación Mensual (Recargos)'
        verbose_name_plural = 'Observaciones Mensuales (Recargos)'

    def __str__(self):
        return f"Emp {self.empleado_id} — {self.year}/{self.month}"


class CoordinadorRecargos(models.Model):
    nombre    = models.CharField(max_length=150)
    documento = models.CharField(max_length=20, unique=True)
    cargo     = models.CharField(max_length=100, blank=True, default='')
    areas     = models.ManyToManyField(AreaRecargos, blank=True, related_name='coordinadores_recargos')

    class Meta:
        ordering     = ['nombre']
        verbose_name = 'Coordinador (Recargos)'
        verbose_name_plural = 'Coordinadores (Recargos)'

    def __str__(self):
        return f"{self.nombre} ({self.documento})"


class PerfilRecargos(models.Model):
    ROL_CHOICES = [
        ('admin',       'Administrador'),
        ('coordinador', 'Coordinador'),
    ]
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_recargos')
    rol       = models.CharField(max_length=15, choices=ROL_CHOICES, default='coordinador')
    documento = models.CharField(max_length=20, blank=True, default='')
    areas     = models.ManyToManyField(AreaRecargos, blank=True, related_name='coordinadores')

    class Meta:
        verbose_name        = 'Perfil Recargos'
        verbose_name_plural = 'Perfiles Recargos'

    def es_admin(self):
        return self.rol == 'admin' or self.user.is_superuser

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

class HoraExtra(models.Model):
    # Relación lógica con Gentercer (al estar en otra DB, no usamos ForeignKey real de DB)
    empleado_oid = models.IntegerField(verbose_name="ID Empleado (OID)")
    nombre_empleado = models.CharField(max_length=255, verbose_name="Nombre Completo", blank=True)
    documento_empleado = models.CharField(max_length=50, verbose_name="Documento", blank=True)
    
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha de Labores")
    
    # Recargos (Horas laboradas normales con recargo)
    horas_recargo_nocturno = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Recargo Nocturno (35%)")
    horas_recargo_dominical_diurno = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Dominical/Festiva Diurna (75%)")
    horas_recargo_dominical_nocturno = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Dominical/Festiva Nocturna (110%)")
    
    # Horas Extras (Horas adicionales a la jornada)
    horas_extra_diurna = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Extra Diurna (25%)")
    horas_extra_nocturna = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Extra Nocturna (75%)")
    horas_extra_dominical_diurna = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Extra Dominical/Festiva Diurna (100%)")
    horas_extra_dominical_nocturna = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="H. Extra Dominical/Festiva Nocturna (150%)")
    
    # Metadatos
    usuario_registro = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="Registrado por")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Carga de Hora Extra"
        verbose_name_plural = "Carga de Horas Extras y Recargos"
        ordering = ['-fecha', '-fecha_registro']

    def __str__(self):
        return f"{self.documento_empleado} - {self.fecha}"

    @property
    def total_horas_extras(self):
        return (self.horas_extra_diurna + self.horas_extra_nocturna + 
                self.horas_extra_dominical_diurna + self.horas_extra_dominical_nocturna)

    @property
    def total_recargos(self):
        return (self.horas_recargo_nocturno + self.horas_recargo_dominical_diurno + 
                self.horas_recargo_dominical_nocturno)
