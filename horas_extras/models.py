from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

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
