# URLs de la aplicación traslados.

from django.http import HttpResponse
from django.urls import path
from . import views


def _vistaProximamente (request, *args, **kwargs):
	"""Vista provisional para rutas aún no implementadas."""
	return HttpResponse ('Próximamente', status=200)


urlpatterns = [
	path ('', views.VistaMain.as_view (), name='principal'),
	path ('recuperar-contrasena/', views.VistaRecuperarContrasena.as_view (), name='recuperar-contrasena'),

	# ── CRUD de traslados (HTMX) ─────────────────────────────────────────────
	path ('traslados/tabla/', views.VistaTablaTrasladosHTMX.as_view (), name='tabla-traslados'),
	path ('traslados/nuevo/', views.VistaNuevoTrasladoHTMX.as_view (), name='traslado-nuevo'),
	path ('traslados/<int:pk>/editar/', views.VistaEditarTrasladoHTMX.as_view (), name='traslado-editar'),
	path ('traslados/<int:pk>/confirmar-eliminar/', views.VistaConfirmarEliminarHTMX.as_view (), name='traslado-confirmar-eliminar'),
	path ('traslados/<int:pk>/eliminar/', views.VistaEliminarTrasladoHTMX.as_view (), name='traslado-eliminar'),

	# ── Reportes ─────────────────────────────────────────────────────────────
	path ('reportes/excel/', views.VistaReporteExcel.as_view (), name='reporte-excel'),
	path ('perfil/contrasena/', views.VistaCambiarContrasenaPropia.as_view (), name='cambiar-contrasena'),
	path ('usuarios/', views.vistaListaUsuarios, name='usuarios'),
	path ('usuarios/nuevo/', views.vistaCrearUsuario, name='usuario-nuevo'),
	path ('usuarios/<int:pk>/contrasena/', views.vistaCambiarContrasenaUsuario, name='usuario-contrasena'),
	path ('usuarios/<int:pk>/eliminar/', views.vistaEliminarUsuario, name='usuario-eliminar'),
	path ('sistema/limpiar/', views.vistaLimpiarSistema, name='limpiar-sistema'),
	path ('mes/<int:mes>/cerrar/', views.vistaCerrarMes, name='cerrar-mes'),
]
