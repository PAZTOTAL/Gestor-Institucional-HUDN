# URLs de la aplicación crue_traslados.

from django.urls import path
from django.contrib.auth import views as authViews

from . import views

app_name = 'crue_traslados'

urlpatterns = [
	path ('login/', authViews.LoginView.as_view (), name='login'),
	path ('logout/', authViews.LogoutView.as_view (), name='logout'),
	path ('', views.VistaMain.as_view (), name='principal'),

	# ── CRUD de traslados (HTMX) ─────────────────────────────────────────────
	path ('traslados/tabla/', views.VistaTablaTrasladosHTMX.as_view (), name='tabla-traslados'),
	path ('traslados/nuevo/', views.VistaNuevoTrasladoHTMX.as_view (), name='traslado-nuevo'),
	path ('traslados/<int:pk>/editar/', views.VistaEditarTrasladoHTMX.as_view (), name='traslado-editar'),
	path ('traslados/<int:pk>/clonar/', views.VistaClonarTrasladoHTMX.as_view (), name='traslado-clonar'),
	path ('traslados/<int:pk>/confirmar-eliminar/', views.VistaConfirmarEliminarHTMX.as_view (), name='traslado-confirmar-eliminar'),
	path ('traslados/<int:pk>/eliminar/', views.VistaEliminarTrasladoHTMX.as_view (), name='traslado-eliminar'),

	# ── Reportes ─────────────────────────────────────────────────────────────
	path ('reportes/excel/', views.VistaReporteExcel.as_view (), name='reporte-excel'),

	# ── Importar ──────────────────────────────────────────────────────────────
	path ('importar/excel/', views.VistaImportarExcel.as_view (), name='importar-excel'),

	# ── Gestión de cuenta ─────────────────────────────────────────────────────
	path ('perfil/contrasena/', views.VistaCambiarContrasena.as_view (), name='cambiar-contrasena'),
]
