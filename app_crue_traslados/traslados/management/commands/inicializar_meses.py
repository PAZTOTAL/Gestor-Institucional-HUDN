"""
Comando de gestión: inicializar_meses.

Garantiza que existan las 12 filas de ControlMes (una por cada mes del año)
con estado ABIERTO por defecto. Es idempotente: no modifica filas existentes.
"""

from django.core.management.base import BaseCommand

from traslados.models import ControlMes


class Command (BaseCommand):
	"""Crea las 12 filas de ControlMes si aún no existen."""

	help = 'Inicializa los 12 registros de ControlMes con estado ABIERTO.'

	def handle (self, *args, **options):
		"""Ejecuta la inicialización de los meses del año."""
		creados = 0
		for numeroMes in range (1, 13):
			_, fueCreado = ControlMes.objects.get_or_create (
				mes=numeroMes,
				defaults={'estado': 'ABIERTO'},
			)
			if fueCreado:
				creados += 1

		if creados:
			self.stdout.write (
				self.style.SUCCESS (f'{creados} mes(es) inicializado(s) correctamente.')
			)
		else:
			self.stdout.write ('Todos los meses ya estaban inicializados.')
