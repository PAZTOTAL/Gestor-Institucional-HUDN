"""
Vistas de la aplicación traslados.
"""

import calendar
import datetime
import functools
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .forms import FormularioCambiarContrasenaPropia, FormularioCambiarContrasenaUsuario, FormularioCrearUsuario, FormularioTraslado
from .models import ControlMes, TrasladoPaciente
from .services.report_excel import generarExcel

Usuario = get_user_model ()
logger = logging.getLogger (__name__)

# ─── Nombres de meses en español ─────────────────────────────────────────────

NOMBRES_MESES = [
	(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
	(5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
	(9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


# ─── Decorador de acceso exclusivo para DIRECTOR ─────────────────────────────

def directorRequerido (funcion):
	"""Decorador que restringe el acceso a usuarios con rol DIRECTOR.

	Redirige a login si no hay sesión activa; retorna HTTP 403 si el usuario
	autenticado no tiene el rol DIRECTOR.
	"""
	@functools.wraps (funcion)
	@login_required
	def envoltura (request, *args, **kwargs):
		"""Verifica el rol del usuario antes de ejecutar la vista."""
		try:
			rolUsuario = request.user.rol
		except Exception:
			rolUsuario = None

		if rolUsuario != 'DIRECTOR':
			return HttpResponseForbidden ('Acceso denegado. Se requiere rol DIRECTOR.')

		return funcion (request, *args, **kwargs)

	return envoltura


# ─── Vista principal ─────────────────────────────────────────────────────────

class VistaMain (LoginRequiredMixin, TemplateView):
	"""Vista principal del sistema: muestra el sidebar, barra de título y tabla de registros."""

	template_name = 'traslados/main.html'

	def get_context_data (self, **kwargs):
		"""Construye el contexto con filtros validados, estado del mes y datos del usuario."""
		contexto = super ().get_context_data (**kwargs)

		hoy = datetime.date.today ()
		mesActual = hoy.month
		erroresFiltro = []

		# ── Leer parámetros de la query string ──────────────────────────────
		mesParam = self.request.GET.get ('mes', '')
		diaDesdeParam = self.request.GET.get ('dia_desde', '')
		diaHastaParam = self.request.GET.get ('dia_hasta', '')

		# ── Parsear mes ──────────────────────────────────────────────────────
		try:
			mesSeleccionado = int (mesParam) if mesParam else mesActual
		except ValueError:
			mesSeleccionado = mesActual

		# ── Validar mes no mayor al mes actual ───────────────────────────────
		if mesSeleccionado > mesActual:
			erroresFiltro.append (
				f'Solo se permiten meses hasta el mes actual ({mesActual}).'
			)
			mesSeleccionado = mesActual

		# ── Calcular rango de días válido para el mes seleccionado ───────────
		diasEnMes = calendar.monthrange (hoy.year, mesSeleccionado) [1]

		# ── Parsear día desde ────────────────────────────────────────────────
		try:
			diaDesde = int (diaDesdeParam) if diaDesdeParam else 1
		except ValueError:
			diaDesde = 1

		# ── Parsear día hasta ────────────────────────────────────────────────
		try:
			diaHasta = int (diaHastaParam) if diaHastaParam else diasEnMes
		except ValueError:
			diaHasta = diasEnMes

		# ── Validar rango de días ────────────────────────────────────────────
		if diaDesde < 1 or diaDesde > diasEnMes:
			erroresFiltro.append (
				f'El día desde debe estar entre 1 y {diasEnMes}.'
			)
			diaDesde = 1

		if diaHasta < 1 or diaHasta > diasEnMes:
			erroresFiltro.append (
				f'El día hasta debe estar entre 1 y {diasEnMes}.'
			)
			diaHasta = diasEnMes

		if diaDesde > diaHasta:
			erroresFiltro.append (
				'El día desde no puede ser mayor que el día hasta.'
			)
			diaDesde = 1
			diaHasta = diasEnMes

		# ── Obtener estado del mes seleccionado ──────────────────────────────
		try:
			estadoMes = ControlMes.objects.get (mes=mesSeleccionado)
		except ControlMes.DoesNotExist:
			estadoMes = None

		# ── Obtener rol del usuario ──────────────────────────────────────────
		try:
			rolUsuario = self.request.user.rol
		except Exception:
			rolUsuario = 'FUNCIONARIO'

		contexto.update ({
			'mesSeleccionado': mesSeleccionado,
			'diaDesde': diaDesde,
			'diaHasta': diaHasta,
			'estadoMes': estadoMes,
			'rolUsuario': rolUsuario,
			'fechaActual': hoy,
			'erroresFiltro': erroresFiltro,
			'meses': NOMBRES_MESES,
			'mesActual': mesActual,
			'diasEnMes': diasEnMes,
		})

		return contexto


# ─── Vista de recuperación de contraseña ─────────────────────────────────────

class VistaRecuperarContrasena (View):
	"""Muestra el formulario de recuperación de contraseña y procesa el envío."""

	MENSAJE_GENERICO = (
		'Para restablecer tu contraseña, comunícate con el DIRECTOR del sistema. '
		'Él podrá asignarte una nueva contraseña de acceso.'
	)

	def get (self, request):
		"""Renderiza el formulario de recuperación de contraseña."""
		return render (request, 'traslados/password_recovery.html')

	def post (self, request):
		"""Procesa el formulario y retorna siempre el mismo mensaje genérico."""
		return render (request, 'traslados/password_recovery.html', {
			'mensaje': self.MENSAJE_GENERICO,
		})


# ─── Vista: cambiar contraseña propia ────────────────────────────────────────

class VistaCambiarContrasenaPropia (LoginRequiredMixin, View):
	"""Muestra el formulario de cambio de contraseña propia (GET) y procesa el cambio (POST)."""

	def get (self, request):
		"""Renderiza el formulario vacío de cambio de contraseña propia."""
		formulario = FormularioCambiarContrasenaPropia ()
		return render (request, 'traslados/cambiar_contrasena.html', {
			'formulario': formulario,
		})

	def post (self, request):
		"""Valida la contraseña actual y actualiza la contraseña si los datos son válidos."""
		formulario = FormularioCambiarContrasenaPropia (request.POST)
		if formulario.is_valid ():
			contrasenaActual = formulario.cleaned_data ['contrasena_actual']
			nuevaContrasena = formulario.cleaned_data ['nueva_contrasena']

			if not request.user.check_password (contrasenaActual):
				formulario.add_error ('contrasena_actual', 'La contraseña actual es incorrecta.')
				return render (request, 'traslados/cambiar_contrasena.html', {
					'formulario': formulario,
				})

			request.user.set_password (nuevaContrasena)
			request.user.save ()

			from django.contrib.auth import update_session_auth_hash
			update_session_auth_hash (request, request.user)

			return render (request, 'traslados/cambiar_contrasena.html', {
				'formulario': FormularioCambiarContrasenaPropia (),
				'exito': True,
			})

		return render (request, 'traslados/cambiar_contrasena.html', {
			'formulario': formulario,
		})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _obtenerFiltros (request):
	"""Extrae y valida los parámetros de filtro mes/dia_desde/dia_hasta del request."""
	hoy = datetime.date.today ()
	mesActual = hoy.month

	try:
		mes = int (request.GET.get ('mes', mesActual))
	except (ValueError, TypeError):
		mes = mesActual

	if mes < 1 or mes > 12:
		mes = mesActual

	diasEnMes = calendar.monthrange (hoy.year, mes) [1]

	try:
		diaDesde = int (request.GET.get ('dia_desde', 1))
	except (ValueError, TypeError):
		diaDesde = 1

	try:
		diaHasta = int (request.GET.get ('dia_hasta', diasEnMes))
	except (ValueError, TypeError):
		diaHasta = diasEnMes

	diaDesde = max (1, min (diaDesde, diasEnMes))
	diaHasta = max (1, min (diaHasta, diasEnMes))

	if diaDesde > diaHasta:
		diaDesde = 1
		diaHasta = diasEnMes

	return mes, diaDesde, diaHasta, hoy.year


def _obtenerContextoTabla (mes, diaDesde, diaHasta, anio):
	"""Construye el queryset filtrado y el estado del mes para el partial de tabla."""
	fechaDesde = datetime.date (anio, mes, diaDesde)
	fechaHasta = datetime.date (anio, mes, diaHasta)

	registros = TrasladoPaciente.objects.filter (
		mes=mes,
		fecha__gte=fechaDesde,
		fecha__lte=fechaHasta,
	)

	try:
		controlMes = ControlMes.objects.get (mes=mes)
	except ControlMes.DoesNotExist:
		controlMes = None

	mesCerrado = controlMes.estaCerrado () if controlMes else False

	return {
		'registros': registros,
		'controlMes': controlMes,
		'mesCerrado': mesCerrado,
		'mes': mes,
		'diaDesde': diaDesde,
		'diaHasta': diaHasta,
	}


def _mesCerrado (mes):
	"""Retorna True si el ControlMes para el mes dado está CERRADO."""
	try:
		control = ControlMes.objects.get (mes=mes)
		return control.estaCerrado ()
	except ControlMes.DoesNotExist:
		return False


# ─── Vista HTMX: tabla de registros ──────────────────────────────────────────

class VistaTablaTrasladosHTMX (LoginRequiredMixin, View):
	"""Retorna el partial HTML de la tabla de registros filtrados."""

	def get (self, request):
		"""Aplica filtros y renderiza el partial table.html."""
		mes, diaDesde, diaHasta, anio = _obtenerFiltros (request)
		contexto = _obtenerContextoTabla (mes, diaDesde, diaHasta, anio)
		return render (request, 'traslados/partials/table.html', contexto)


# ─── Vista HTMX: crear traslado ───────────────────────────────────────────────

class VistaNuevoTrasladoHTMX (LoginRequiredMixin, View):
	"""Muestra el formulario vacío (GET) y crea un nuevo registro (POST)."""

	def _obtenerMesActivo (self, request):
		"""Extrae el mes activo del request."""
		try:
			return int (request.GET.get ('mes', datetime.date.today ().month))
		except (ValueError, TypeError):
			return datetime.date.today ().month

	def get (self, request):
		"""Retorna el modal con formulario vacío; 403 si el mes está cerrado."""
		mes = self._obtenerMesActivo (request)
		if _mesCerrado (mes):
			return HttpResponse ('El mes está cerrado. No se pueden crear registros.', status=403)

		formulario = FormularioTraslado (initial={'fecha': datetime.date.today ()})
		return render (request, 'traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'crear',
			'mes': mes,
		})

	def post (self, request):
		"""Valida y guarda el nuevo registro; retorna tabla actualizada o modal con errores."""
		try:
			mes = int (request.POST.get ('mes', datetime.date.today ().month))
		except (ValueError, TypeError):
			mes = datetime.date.today ().month

		if _mesCerrado (mes):
			return HttpResponse ('El mes está cerrado. No se pueden crear registros.', status=403)

		formulario = FormularioTraslado (request.POST)
		if formulario.is_valid ():
			try:
				formulario.save ()
			except ValidationError as e:
				formulario.add_error (None, e)
				return render (request, 'traslados/partials/modal_form.html', {
					'formulario': formulario,
					'accion': 'crear',
					'mes': mes,
				})

			diaDesde = 1
			diaHasta = calendar.monthrange (datetime.date.today ().year, mes) [1]
			contexto = _obtenerContextoTabla (mes, diaDesde, diaHasta, datetime.date.today ().year)
			respuesta = render (request, 'traslados/partials/table.html', contexto)
			respuesta ['HX-Trigger'] = 'cerrarModal'
			return respuesta

		return render (request, 'traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'crear',
			'mes': mes,
		})


# ─── Vista HTMX: editar traslado ──────────────────────────────────────────────

class VistaEditarTrasladoHTMX (LoginRequiredMixin, View):
	"""Muestra el formulario precargado (GET) y actualiza el registro (POST)."""

	def get (self, request, pk):
		"""Retorna el modal con datos del registro; 404 si no existe; 403 si mes cerrado."""
		registro = get_object_or_404 (TrasladoPaciente, pk=pk)
		if _mesCerrado (registro.mes):
			return HttpResponse ('El mes está cerrado. No se pueden editar registros.', status=403)

		formulario = FormularioTraslado (instance=registro)
		return render (request, 'traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'editar',
			'registro': registro,
			'mes': registro.mes,
		})

	def post (self, request, pk):
		"""Valida y guarda los cambios; retorna tabla actualizada o modal con errores."""
		registro = get_object_or_404 (TrasladoPaciente, pk=pk)
		if _mesCerrado (registro.mes):
			return HttpResponse ('El mes está cerrado. No se pueden editar registros.', status=403)

		formulario = FormularioTraslado (request.POST, instance=registro)
		if formulario.is_valid ():
			try:
				formulario.save ()
			except ValidationError as e:
				formulario.add_error (None, e)
				return render (request, 'traslados/partials/modal_form.html', {
					'formulario': formulario,
					'accion': 'editar',
					'registro': registro,
					'mes': registro.mes,
				})

			mes = registro.mes
			diaDesde = 1
			diaHasta = calendar.monthrange (datetime.date.today ().year, mes) [1]
			contexto = _obtenerContextoTabla (mes, diaDesde, diaHasta, datetime.date.today ().year)
			respuesta = render (request, 'traslados/partials/table.html', contexto)
			respuesta ['HX-Trigger'] = 'cerrarModal'
			return respuesta

		return render (request, 'traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'editar',
			'registro': registro,
			'mes': registro.mes,
		})


# ─── Vista HTMX: confirmar eliminación ───────────────────────────────────────

class VistaConfirmarEliminarHTMX (LoginRequiredMixin, View):
	"""Muestra el partial de confirmación de eliminación."""

	def get (self, request, pk):
		"""Retorna el partial de confirmación; 404 si no existe; 403 si mes cerrado."""
		registro = get_object_or_404 (TrasladoPaciente, pk=pk)
		if _mesCerrado (registro.mes):
			return HttpResponse ('El mes está cerrado. No se pueden eliminar registros.', status=403)

		return render (request, 'traslados/partials/confirmar_eliminar.html', {
			'registro': registro,
		})


# ─── Vista HTMX: eliminar traslado ────────────────────────────────────────────

class VistaEliminarTrasladoHTMX (LoginRequiredMixin, View):
	"""Elimina un registro y retorna la tabla actualizada."""

	def delete (self, request, pk):
		"""Elimina el registro; retorna tabla actualizada; 404 si no existe; 403 si mes cerrado."""
		registro = get_object_or_404 (TrasladoPaciente, pk=pk)
		mes = registro.mes

		if _mesCerrado (mes):
			return HttpResponse ('El mes está cerrado. No se pueden eliminar registros.', status=403)

		registro.delete ()

		diaDesde = 1
		diaHasta = calendar.monthrange (datetime.date.today ().year, mes) [1]
		contexto = _obtenerContextoTabla (mes, diaDesde, diaHasta, datetime.date.today ().year)
		respuesta = render (request, 'traslados/partials/table.html', contexto)
		respuesta ['HX-Trigger'] = 'cerrarModal'
		return respuesta


# ─── Vista: cerrar mes ────────────────────────────────────────────────────────

@directorRequerido
def vistaCerrarMes (request, mes):
	"""Cierra el mes indicado (solo DIRECTOR, solo POST).

	Cambia ControlMes.estado a CERRADO, registra la fecha y el usuario que cerró.
	Retorna 404 si no existe el ControlMes para el mes dado.
	"""
	if request.method != 'POST':
		return HttpResponse ('Método no permitido.', status=405)

	controlMes = get_object_or_404 (ControlMes, mes=mes)
	controlMes.estado = 'CERRADO'
	controlMes.fecha_cierre = timezone.now ()
	controlMes.cerrado_por = request.user
	controlMes.save ()

	return redirect ('principal')


# ─── Vista: reporte Excel ─────────────────────────────────────────────────────

class VistaReporteExcel (LoginRequiredMixin, View):
	"""Genera y descarga el reporte Excel de traslados filtrados por mes y rango de días."""

	def get (self, request):
		"""Lee los parámetros de filtro, genera el Excel y retorna la respuesta de descarga."""
		mes, diaDesde, diaHasta, anio = _obtenerFiltros (request)

		fechaDesde = datetime.date (anio, mes, diaDesde)
		fechaHasta = datetime.date (anio, mes, diaHasta)

		queryset = TrasladoPaciente.objects.filter (
			mes=mes,
			fecha__gte=fechaDesde,
			fecha__lte=fechaHasta,
		)

		try:
			bytesArchivo, nombreArchivo = generarExcel (queryset, mes)
		except Exception as exc:
			logger.exception ('Error al generar el reporte Excel: %s', exc)
			return render (request, 'traslados/error_reporte.html', {
				'mensaje': 'Ocurrió un error al generar el reporte Excel. Por favor, intente nuevamente.',
			}, status=500)

		respuesta = HttpResponse (
			bytesArchivo,
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)
		respuesta ['Content-Disposition'] = f'attachment; filename="{nombreArchivo}"'
		return respuesta


# ─── Vista: listado de usuarios ───────────────────────────────────────────────

@directorRequerido
def vistaListaUsuarios (request):
	"""Muestra el listado de todos los usuarios con su nombre de usuario y rol (solo DIRECTOR)."""
	usuarios = Usuario.objects.all ().order_by ('username')
	return render (request, 'traslados/user_management.html', {
		'usuarios': usuarios,
		'formulario': FormularioCrearUsuario (),
	})


# ─── Vista: crear usuario ─────────────────────────────────────────────────────

@directorRequerido
def vistaCrearUsuario (request):
	"""Muestra el formulario de creación (GET) y crea un nuevo usuario (POST) (solo DIRECTOR).

	Captura IntegrityError para informar al usuario si el username ya existe.
	"""
	if request.method == 'GET':
		formulario = FormularioCrearUsuario ()
		usuarios = Usuario.objects.all ().order_by ('username')
		return render (request, 'traslados/user_management.html', {
			'formulario': formulario,
			'usuarios': usuarios,
		})

	formulario = FormularioCrearUsuario (request.POST)
	if formulario.is_valid ():
		username = formulario.cleaned_data ['username']
		password = formulario.cleaned_data ['password']
		rol = formulario.cleaned_data ['rol']

		try:
			nuevoUsuario = Usuario.objects.create_user (username=username, password=password, rol=rol)
			return redirect ('usuarios')
		except IntegrityError:
			formulario.add_error ('username', 'Ya existe un usuario con ese nombre de usuario.')

	usuarios = Usuario.objects.all ().order_by ('username')
	return render (request, 'traslados/user_management.html', {
		'formulario': formulario,
		'usuarios': usuarios,
	})


# ─── Vista: cambiar contraseña de usuario ────────────────────────────────────

@directorRequerido
def vistaCambiarContrasenaUsuario (request, pk):
	"""Muestra el formulario de cambio de contraseña (GET) y actualiza la contraseña (POST) (solo DIRECTOR).

	No requiere la contraseña actual; el DIRECTOR puede cambiar la contraseña de cualquier usuario.
	Retorna 404 si el usuario no existe.
	"""
	usuarioObjetivo = get_object_or_404 (Usuario, pk=pk)

	if request.method == 'GET':
		formulario = FormularioCambiarContrasenaUsuario ()
		return render (request, 'traslados/cambiar_contrasena_usuario.html', {
			'formulario': formulario,
			'usuarioObjetivo': usuarioObjetivo,
		})

	formulario = FormularioCambiarContrasenaUsuario (request.POST)
	if formulario.is_valid ():
		nuevaContrasena = formulario.cleaned_data ['nueva_contrasena']
		usuarioObjetivo.set_password (nuevaContrasena)
		usuarioObjetivo.save ()
		return redirect ('usuarios')

	return render (request, 'traslados/cambiar_contrasena_usuario.html', {
		'formulario': formulario,
		'usuarioObjetivo': usuarioObjetivo,
	})


# ─── Vista: limpiar datos del sistema ────────────────────────────────────────

@directorRequerido
def vistaLimpiarSistema (request):
	"""Muestra la página de limpieza anual (GET) y ejecuta la limpieza (POST) (solo DIRECTOR).

	GET: muestra sugerencia de generar reportes y el formulario de confirmación.
	POST confirmado: elimina todos los TrasladoPaciente y restablece todos los ControlMes a ABIERTO.
	POST cancelado: redirige a la vista principal sin modificar datos.
	"""
	if request.method == 'GET':
		return render (request, 'traslados/limpiar_sistema.html')

	# ── POST: verificar si el usuario confirmó o canceló ────────────────────
	accion = request.POST.get ('accion', '')

	if accion == 'cancelar':
		return redirect ('principal')

	if accion == 'confirmar':
		_ejecutarLimpieza ()
		from django.contrib import messages
		messages.success (request, 'Limpieza completada: todos los registros han sido eliminados y los meses han sido restablecidos a ABIERTO.')
		return redirect ('principal')

	# Acción desconocida: redirigir sin modificar
	return redirect ('principal')


def _ejecutarLimpieza ():
	"""Elimina todos los TrasladoPaciente y restablece todos los ControlMes a ABIERTO."""
	TrasladoPaciente.objects.all ().delete ()
	ControlMes.objects.all ().update (estado='ABIERTO', fecha_cierre=None, cerrado_por=None)


# ─── Vista: eliminar usuario ──────────────────────────────────────────────────

@directorRequerido
def vistaEliminarUsuario (request, pk):
	"""Muestra confirmación de eliminación (GET) y elimina el usuario (POST) (solo DIRECTOR).

	El DIRECTOR no puede eliminarse a sí mismo.
	Retorna 404 si el usuario no existe.
	"""
	usuarioObjetivo = get_object_or_404 (Usuario, pk=pk)

	if request.method == 'GET':
		return render (request, 'traslados/partials/confirmar_eliminar_usuario.html', {
			'usuarioObjetivo': usuarioObjetivo,
		})

	if usuarioObjetivo == request.user:
		usuarios = Usuario.objects.all ().order_by ('username')
		return render (request, 'traslados/user_management.html', {
			'usuarios': usuarios,
			'formulario': FormularioCrearUsuario (),
			'errorEliminar': 'No puede eliminar su propio usuario.',
		})

	usuarioObjetivo.delete ()
	return redirect ('usuarios')
