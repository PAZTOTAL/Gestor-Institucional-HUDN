"""
Configuración de la aplicación traslados.
"""

from django.apps import AppConfig


class AppTrasladosConfig (AppConfig):
	"""Configuración principal de la app de registro de traslados de pacientes."""

	default_auto_field = 'django.db.models.BigAutoField'
	name = 'traslados'
	verbose_name = 'Registro de Traslados'

	def ready (self):
		"""Registra señales y conecta el inicializador de meses al evento post_migrate."""
		import traslados.models  # noqa: F401 — registra señales post_save

		from django.db.models.signals import post_migrate
		from django.apps import apps

		def inicializarMeses (sender, **kwargs):
			"""Crea las 12 filas de ControlMes si aún no existen tras cada migración."""
			ControlMes = apps.get_model ('traslados', 'ControlMes')
			for numeroMes in range (1, 13):
				ControlMes.objects.get_or_create (
					mes=numeroMes,
					defaults={'estado': 'ABIERTO'},
				)

		post_migrate.connect (inicializarMeses, sender=self)
