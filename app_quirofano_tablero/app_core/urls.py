from django.urls import path
from django.views.generic import RedirectView

from .vistas import ActualizarPacienteVista, AgregarPacienteVista, AplicarEstadoVista, CargarProgramadosVista, GestionVista, TableroFragmentoVista, TableroVista

urlpatterns = [
	path ('', RedirectView.as_view (url='/tablero/', permanent=False), name='inicio'),
	path ('tablero/', TableroVista.as_view (), name='tablero'),
	path ('tablero/fragmento/', TableroFragmentoVista.as_view (), name='tablero-fragmento'),
	path ('gestion/', GestionVista.as_view (), name='gestion'),
	path ('gestion/pacientes/agregar/', AgregarPacienteVista.as_view (), name='agregar-paciente'),
	path ('gestion/pacientes/actualizar/', ActualizarPacienteVista.as_view (), name='actualizar-paciente'),
	path ('gestion/programados/cargar/', CargarProgramadosVista.as_view (), name='cargar-programados'),
	path ('gestion/sesiones/estado/', AplicarEstadoVista.as_view (), name='aplicar-estado'),
]
