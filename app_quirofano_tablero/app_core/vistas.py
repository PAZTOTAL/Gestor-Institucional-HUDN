import logging

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from app_autenticacion.mixins import LoginRequeridoMixin
from app_notificaciones.servicios import NotificacionServicio

from .models import EstadoQuirurgico, Paciente, Sesion
from .utils import Utils
from .servicios import SesionServicio, coloresEstado, obtenerSesionesVisibles


logger = logging.getLogger (__name__)


class GestionVista (LoginRequeridoMixin, View):
	"""Panel de gestión principal: muestra pacientes y sesiones activas."""

	def get (self, request):
		"""Retorna el panel con pacientes, sesiones activas y lista de estados."""
		contexto = _contextoGestion ()
		return render (request, 'gestion/gestion.html', contexto)


class AplicarEstadoVista (LoginRequeridoMixin, View):
	"""Aplica un nuevo estado quirúrgico a la sesión de un paciente."""

	def post (self, request):
		"""Recibe pacienteId y estado; actualiza la sesión y retorna fragmento HTMX."""
		pacienteId = request.POST.get ('pacienteId')
		estado     = request.POST.get ('estado')

		if not pacienteId or not estado:
			return HttpResponse ('Datos incompletos.', status=400)

		paciente = get_object_or_404 (Paciente, pk=pacienteId)

		try:
			servicio = SesionServicio ()
			sesion   = servicio.aplicarEstado (paciente, estado)
			NotificacionServicio ().notificarCambioEstado (paciente, estado)
		except ValidationError as e:
			return HttpResponse (str (e), status=400)
		except Exception as e:
			print (f"+++ Error al aplicar estado: {e}")
			logger.error (f"Error al aplicar estado: {e}")
			return HttpResponse ('Error interno al actualizar el estado.', status=500)

		return self._renderizarFragmento (request)

	def _renderizarFragmento (self, request):
		"""Construye el contexto y renderiza el fragmento de tablas."""
		return render (request, 'gestion/fragmento_tablas.html', _contextoGestion ())


class ActualizarPacienteVista (LoginRequeridoMixin, View):
	"""Actualiza la identificación de un paciente y retorna el fragmento de tablas."""

	def post (self, request):
		"""Recibe pacienteId, nuevaIdentificacion y opcionalmente labelOtro/estadoOtro/telefono; persiste y retorna fragmento HTMX."""
		import re
		pacienteId          = request.POST.get ('pacienteId')
		nuevaIdentificacion = request.POST.get ('nuevaIdentificacion', '').strip ()
		labelOtro           = request.POST.get ('labelOtro', '').strip ()
		estadoOtro          = request.POST.get ('estadoOtro', '').strip ()
		telefono            = request.POST.get ('telefono', '').strip () or None

		if not pacienteId or not nuevaIdentificacion:
			return HttpResponse ('Datos incompletos.', status=400)

		if telefono and not re.fullmatch (r'\d{10}', telefono):
			return HttpResponse ('El teléfono debe tener exactamente 10 dígitos numéricos.', status=400)

		paciente = get_object_or_404 (Paciente, pk=pacienteId)
		paciente.identificacion = nuevaIdentificacion
		paciente.telefono       = telefono
		paciente.save ()

		# Solo modificar estado/label si el usuario lo cambió explícitamente
		if estadoOtro and labelOtro:
			try:
				SesionServicio ().aplicarEstado (paciente, 'OTRO', labelOtro=labelOtro)
				NotificacionServicio ().notificarCambioEstado (paciente, 'OTRO')
			except Exception as e:
				logger.error (f"Error al aplicar estado OTRO desde modal: {e}")

		contexto = _contextoGestion ()
		return render (request, 'gestion/fragmento_tablas.html', contexto)


class AgregarPacienteVista (LoginRequeridoMixin, View):
	"""Agrega un paciente de urgencias y retorna el fragmento de tablas actualizado."""

	def post (self, request):
		"""Crea un Paciente con origen URGENCIAS y retorna fragmento HTMX."""
		identificacion = request.POST.get ('identificacion', '').strip ()
		nombre         = request.POST.get ('nombre', '').strip () or None

		if not identificacion:
			return HttpResponse ('La identificación es requerida.', status=400)

		Paciente.objects.get_or_create (
			identificacion=identificacion,
			defaults={'nombre': nombre, 'origen': 'URGENCIAS'},
		)

		return render (request, 'gestion/fragmento_tablas.html', _contextoGestion ())


class TableroVista (View):
	"""Tablero público de seguimiento quirúrgico para pantallas TV."""

	def get (self, request):
		"""Retorna el tablero completo con layout TV, sin autenticación."""
		contexto = {
			'sesiones':      obtenerSesionesVisibles (),
			'coloresEstado': coloresEstado,
		}
		return render (request, 'tablero/tablero.html', contexto)


class TableroFragmentoVista (View):
	"""Retorna solo el fragmento de lista para polling HTMX del tablero."""

	def get (self, request):
		"""Retorna el fragmento HTML con las sesiones visibles actualizadas."""
		contexto = {
			'sesiones':      obtenerSesionesVisibles (),
			'coloresEstado': coloresEstado,
		}
		return render (request, 'tablero/fragmento.html', contexto)


class CargarProgramadosVista (LoginRequeridoMixin, View):
	"""Limpia la tabla de pacientes y carga los programados desde la fuente externa."""

	_ejecutando = False

	def post (self, request):
		"""Ejecuta Utils.cargarPacientesProgramadosCirugia() y retorna fragmento actualizado."""
		if CargarProgramadosVista._ejecutando:
			return HttpResponse ('Carga en progreso, espere.', status=409)

		try:
			CargarProgramadosVista._ejecutando = True
			Utils.cargarPacientesProgramadosCirugia ()
		except Exception as e:
			logger.error (f"Error al cargar pacientes programados: {e}")
			return HttpResponse ('Error al cargar pacientes programados.', status=500)
		finally:
			CargarProgramadosVista._ejecutando = False

		return render (request, 'gestion/fragmento_tablas.html', _contextoGestion ())


def _contextoGestion ():
	"""Construye el contexto compartido para las vistas del panel de gestión."""
	sesiones = list (obtenerSesionesVisibles ())
	sesionPorPaciente = {s.paciente_id: s for s in sesiones}

	# Pacientes con sesión activa, en el mismo orden que sesionesActivas
	pacientesConSesion = [s.paciente for s in sesiones]
	idsPacientesConSesion = {p.pk for p in pacientesConSesion}

	# Pacientes sin sesión activa al final, ordenados por identificacion
	pacientesSinSesion = list (
		Paciente.objects.exclude (pk__in=idsPacientesConSesion).order_by ('identificacion')
	)

	pacientes = pacientesConSesion + pacientesSinSesion

	return {
		'pacientes':         pacientes,
		'sesionesActivas':   sesiones,
		'estados':           EstadoQuirurgico,
		'sesionPorPaciente': sesionPorPaciente,
	}



