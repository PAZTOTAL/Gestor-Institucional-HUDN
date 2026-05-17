"""
Configuración de la aplicación crue_traslados.
"""

from django.apps import AppConfig


class AppCrueTrasladosConfig (AppConfig):
	"""Configuración principal de la app de registro de traslados de pacientes."""
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'crue_traslados'
	verbose_name = 'Registro de Traslados CRUE'
