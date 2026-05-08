# Registro de modelos en el panel de administración de Django.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ControlMes, TrasladoPaciente, Usuario


class AdminUsuario (UserAdmin):
	"""Configuración del panel de administración para el modelo Usuario."""

	list_display = ['username', 'nombre', 'correo', 'rol', 'is_active']
	list_filter = ['rol', 'is_active']
	search_fields = ['username', 'nombre', 'correo']

	fieldsets = UserAdmin.fieldsets + (
		('Datos adicionales', {'fields': ('nombre', 'correo', 'rol')}),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		('Datos adicionales', {'fields': ('nombre', 'correo', 'rol')}),
	)


class AdminControlMes (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo ControlMes."""

	list_display = ['mes', 'estado', 'fecha_cierre', 'cerrado_por']
	list_filter = ['estado']
	ordering = ['mes']


class AdminTrasladoPaciente (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo TrasladoPaciente."""

	list_display = [
		'fecha',
		'mes',
		'nombre_paciente',
		'documento',
		'servicio',
		'destino',
		'conductor',
		'ambulancia',
	]
	list_filter = ['mes', 'servicio', 'destino']
	search_fields = ['nombre_paciente', 'documento', 'conductor']
	ordering = ['fecha', 'hora_reporte']


admin.site.register (Usuario, AdminUsuario)
admin.site.register (ControlMes, AdminControlMes)
admin.site.register (TrasladoPaciente, AdminTrasladoPaciente)
