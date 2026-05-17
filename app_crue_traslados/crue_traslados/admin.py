# Registro de modelos en el panel de administración de Django.

from django.contrib import admin

from .models import Traslado


class AdminTraslado (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo Traslado."""

	list_display = [
		'fecha_reporte',
		'nombre_paciente',
		'documento',
		'servicio',
		'destino',
		'aux_enfermeria',
		'conductor',
		'ambulancia',
	]
	list_filter = ['servicio', 'destino']
	search_fields = ['nombre_paciente', 'documento', 'conductor']
	ordering = ['-fecha_reporte']


admin.site.register (Traslado, AdminTraslado)
