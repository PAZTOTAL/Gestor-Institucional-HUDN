"""
Modelos de la aplicación crue_traslados.

Define la entidad principal del sistema de registro de traslados: Traslado.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ─── Registro de traslado de paciente ────────────────────────────────────────

class Traslado (models.Model):
	"""Representa un registro de servicio de traslado de paciente."""

	fecha_reporte = models.DateTimeField ()
	fecha_egreso = models.DateTimeField (null=True, blank=True)
	fecha_ingreso = models.DateTimeField (null=True, blank=True)
	nombre_paciente = models.CharField (max_length=255)
	documento = models.CharField (max_length=50)
	servicio = models.CharField (max_length=100, blank=True, default='')
	quien_reporta = models.CharField (max_length=100, blank=True, default='')
	destino = models.CharField (max_length=100, blank=True, default='')
	procedimiento = models.CharField (max_length=255, blank=True, default='')
	medico = models.CharField (max_length=100, blank=True, default='')
	aux_enfermeria = models.CharField (max_length=100, blank=True, default='')
	conductor = models.CharField (max_length=100, blank=True, default='')
	radio_operador = models.CharField (max_length=100, blank=True, default='')
	ambulancia = models.CharField (max_length=100, blank=True, default='')
	observacion = models.TextField (blank=True, default='')
	mes = models.IntegerField (editable=False)

	class Meta:
		db_table = 'cruetraslados_traslado'
		ordering = ['-fecha_reporte']
		indexes = [
			models.Index (fields=['mes']),
			models.Index (fields=['fecha_reporte']),
		]
		verbose_name = 'Traslado'
		verbose_name_plural = 'Traslados'

	def __str__ (self):
		"""Retorna representación legible del traslado."""
		return f"{self.fecha_reporte} – {self.nombre_paciente}"

	def clean (self):
		"""Valida que la fecha de reporte no sea futura."""
		if self.fecha_reporte:
			fechaLocal = timezone.localtime (self.fecha_reporte)
			self.mes = fechaLocal.month
			hoy = datetime.date.today ()
			if fechaLocal.date () > hoy:
				raise ValidationError ({'fecha_reporte': 'La fecha no puede ser futura.'})

	def save (self, *args, **kwargs):
		"""Deriva el campo mes desde fecha_reporte (hora local) y valida antes de persistir."""
		fechaLocal = timezone.localtime (self.fecha_reporte)
		self.mes = fechaLocal.month
		self.full_clean ()
		super ().save (*args, **kwargs)
