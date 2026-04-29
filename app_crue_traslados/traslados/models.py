"""
Modelos de la aplicación traslados.

Define las entidades principales del sistema de registro de traslados:
Usuario, ControlMes y TrasladoPaciente.
"""

import datetime

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


# ─── Modelo de usuario personalizado ─────────────────────────────────────────

class Usuario (AbstractUser):
	"""Modelo de usuario del sistema, extiende AbstractUser con nombre, correo y rol."""

	ROL_CHOICES = [
		('FUNCIONARIO', 'Funcionario'),
		('DIRECTOR', 'Director'),
	]

	nombre = models.CharField (max_length=255, blank=True, default='')
	correo = models.EmailField (blank=True, default='')
	rol = models.CharField (
		max_length=20,
		choices=ROL_CHOICES,
		default='FUNCIONARIO',
	)

	class Meta:
		verbose_name = 'Usuario'
		verbose_name_plural = 'Usuarios'

	def __str__ (self):
		"""Retorna representación legible del usuario."""
		return f"{self.username} ({self.rol})"


# ─── Control de cierre de mes ────────────────────────────────────────────────

class ControlMes (models.Model):
	"""Almacena el estado de apertura o cierre de cada mes del año (1–12)."""

	ESTADO_CHOICES = [
		('ABIERTO', 'Abierto'),
		('CERRADO', 'Cerrado'),
	]

	mes = models.IntegerField (unique=True)
	estado = models.CharField (
		max_length=10,
		choices=ESTADO_CHOICES,
		default='ABIERTO',
	)
	fecha_cierre = models.DateTimeField (null=True, blank=True)
	cerrado_por = models.ForeignKey (
		'Usuario',
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='meses_cerrados',
	)

	class Meta:
		ordering = ['mes']
		verbose_name = 'Control de Mes'
		verbose_name_plural = 'Control de Meses'

	def __str__ (self):
		"""Retorna representación legible del estado del mes."""
		return f"Mes {self.mes}: {self.estado}"

	def estaCerrado (self):
		"""Retorna True si el mes está en estado CERRADO."""
		return self.estado == 'CERRADO'


# ─── Registro de traslado de paciente ────────────────────────────────────────

class TrasladoPaciente (models.Model):
	"""Representa un registro de servicio de traslado de paciente."""

	fecha = models.DateField ()
	hora_reporte = models.TimeField ()
	hora_egreso = models.TimeField (null=True, blank=True)
	hora_ingreso = models.TimeField (null=True, blank=True)
	nombre_paciente = models.CharField (max_length=255)
	documento = models.CharField (max_length=50)
	servicio = models.CharField (max_length=100)
	quien_reporta = models.CharField (max_length=100)
	destino = models.CharField (max_length=100)
	procedimiento = models.CharField (max_length=255)
	medico = models.CharField (max_length=100)
	conductor = models.CharField (max_length=100)
	radio_operador = models.CharField (max_length=100)
	ambulancia = models.CharField (max_length=100)
	observacion = models.TextField (blank=True, default='')
	mes = models.IntegerField (editable=False)

	class Meta:
		ordering = ['fecha', 'hora_reporte']
		indexes = [
			models.Index (fields=['mes']),
			models.Index (fields=['fecha']),
		]
		verbose_name = 'Traslado de Paciente'
		verbose_name_plural = 'Traslados de Pacientes'

	def __str__ (self):
		"""Retorna representación legible del traslado."""
		return f"{self.fecha} – {self.nombre_paciente}"

	def clean (self):
		"""Valida que la fecha no sea futura y que el mes no esté cerrado."""
		if self.fecha:
			self.mes = self.fecha.month
			hoy = datetime.date.today ()
			if self.fecha > hoy:
				raise ValidationError ({'fecha': 'La fecha no puede ser futura.'})
			try:
				control = ControlMes.objects.get (mes=self.mes)
				if control.estaCerrado ():
					raise ValidationError (
						'El mes está cerrado. No se pueden crear ni modificar registros.'
					)
			except ControlMes.DoesNotExist:
				pass

	def save (self, *args, **kwargs):
		"""Deriva el campo mes desde fecha y valida antes de persistir."""
		self.mes = self.fecha.month
		self.full_clean ()
		super ().save (*args, **kwargs)
