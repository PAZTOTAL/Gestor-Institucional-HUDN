"""
Vistas de la aplicación crue_traslados.
"""

import datetime
import logging

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from .decorators import CrueRequiredMixin, crue_required
from .forms import FormularioTraslado
from .models import Traslado
from .services.report_excel import generarExcel

logger = logging.getLogger (__name__)

# ─── Nombres de meses en español ─────────────────────────────────────────────

NOMBRES_MESES = [
	(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
	(5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
	(9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


# ─── Helper: verificar si el usuario es staff ────────────────────────────────

def _esStaff (usuario):
	"""Retorna True si el usuario tiene permisos de staff."""
	return usuario.is_staff


# ─── Vista principal ─────────────────────────────────────────────────────────

class VistaMain (CrueRequiredMixin, TemplateView):
	"""Vista principal del sistema: muestra el sidebar, barra de título y tabla de registros."""

	template_name = 'crue_traslados/main.html'

	def get_context_data (self, **kwargs):
		"""Construye el contexto con filtros validados, estado del mes y datos del usuario."""
		contexto = super ().get_context_data (**kwargs)

		hoy = datetime.date.today ()
		mesActual = hoy.month
		erroresFiltro = []

		# ── Leer parámetros de la query string ──────────────────────────────
		mesParam = self.request.GET.get ('mes', '')
		busqueda = self.request.GET.get ('busqueda', '').strip ()

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

		contexto.update ({
			'mesSeleccionado': mesSeleccionado,
			'busqueda': busqueda,
			'fechaActual': hoy,
			'erroresFiltro': erroresFiltro,
			'meses': NOMBRES_MESES,
			'mesActual': mesActual,
		})

		return contexto


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _obtenerFiltros (request):
	"""Extrae y valida los parámetros de filtro mes, anio y busqueda del request."""
	hoy = datetime.date.today ()
	mesActual = hoy.month

	try:
		mes = int (request.GET.get ('mes', mesActual))
	except (ValueError, TypeError):
		mes = mesActual

	if mes < 1 or mes > 12:
		mes = mesActual

	busqueda = request.GET.get ('busqueda', '').strip ()
	if len (busqueda) > 100:
		busqueda = busqueda [:100]

	return mes, hoy.year, busqueda


def _obtenerContextoTabla (mes, anio, busqueda='', orden='desc', pagina=1, porPagina=15):
	"""Construye el queryset filtrado y paginado para el partial de tabla."""
	import calendar
	from django.core.paginator import Paginator
	from django.utils import timezone as tz

	ordenamiento = '-fecha_reporte' if orden == 'desc' else 'fecha_reporte'

	# Filtrar por rango de fechas del mes usando datetimes timezone-aware
	diasEnMes = calendar.monthrange (anio, mes) [1]
	fechaDesde = tz.make_aware (datetime.datetime (anio, mes, 1, 0, 0, 0))
	fechaHasta = tz.make_aware (datetime.datetime (anio, mes, diasEnMes, 23, 59, 59))

	registrosQs = Traslado.objects.filter (
		fecha_reporte__gte=fechaDesde,
		fecha_reporte__lte=fechaHasta,
	)

	if busqueda:
		registrosQs = registrosQs.filter (
			Q (documento__icontains=busqueda) | Q (nombre_paciente__icontains=busqueda)
		)

	registrosQs = registrosQs.order_by (ordenamiento)

	paginador = Paginator (registrosQs, porPagina)
	paginaObj = paginador.get_page (pagina)

	return {
		'registros': paginaObj,
		'paginaObj': paginaObj,
		'totalRegistros': paginador.count,
		'mes': mes,
		'busqueda': busqueda,
		'orden': orden,
		'pagina': paginaObj.number,
	}


# ─── Vista HTMX: tabla de registros ──────────────────────────────────────────

class VistaTablaTrasladosHTMX (CrueRequiredMixin, View):
	"""Retorna el partial HTML de la tabla de registros filtrados."""

	def get (self, request):
		"""Aplica filtros, orden y paginación, y renderiza el partial table.html."""
		mes, anio, busqueda = _obtenerFiltros (request)
		orden = request.GET.get ('orden', 'desc')
		if orden not in ('desc', 'asc'):
			orden = 'desc'
		try:
			pagina = int (request.GET.get ('pagina', 1))
		except (ValueError, TypeError):
			pagina = 1
		# Paginar: si paginar='0' explícitamente, mostrar todos; de lo contrario paginar a 15
		paginar = request.GET.get ('paginar', '1')
		porPagina = 15 if paginar != '0' else 99999
		contexto = _obtenerContextoTabla (mes, anio, busqueda, orden, pagina, porPagina)
		return render (request, 'crue_traslados/partials/table.html', contexto)


# ─── Vista HTMX: crear traslado ───────────────────────────────────────────────

class VistaNuevoTrasladoHTMX (CrueRequiredMixin, View):
	"""Muestra el formulario vacío (GET) y crea un nuevo registro (POST)."""

	def _obtenerMesActivo (self, request):
		"""Extrae el mes activo del request."""
		try:
			return int (request.GET.get ('mes', datetime.date.today ().month))
		except (ValueError, TypeError):
			return datetime.date.today ().month

	def get (self, request):
		"""Retorna el modal con formulario vacío."""
		mes = self._obtenerMesActivo (request)
		formulario = FormularioTraslado (usuario=request.user)
		return render (request, 'crue_traslados/partials/modal_form.html', {
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

		formulario = FormularioTraslado (request.POST, usuario=request.user)
		if formulario.is_valid ():
			try:
				formulario.save ()
			except ValidationError as e:
				formulario.add_error (None, e)
				return render (request, 'crue_traslados/partials/modal_form.html', {
					'formulario': formulario,
					'accion': 'crear',
					'mes': mes,
				})

			contexto = _obtenerContextoTabla (mes, datetime.date.today ().year)
			respuesta = render (request, 'crue_traslados/partials/table.html', contexto)
			respuesta ['HX-Trigger'] = 'cerrarModal'
			return respuesta

		return render (request, 'crue_traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'crear',
			'mes': mes,
		})


# ─── Vista HTMX: editar traslado ──────────────────────────────────────────────

class VistaEditarTrasladoHTMX (CrueRequiredMixin, View):
	"""Muestra el formulario precargado (GET) y actualiza el registro (POST)."""

	def get (self, request, pk):
		"""Retorna el modal con datos del registro; 404 si no existe."""
		registro = get_object_or_404 (Traslado, pk=pk)
		formulario = FormularioTraslado (instance=registro, usuario=request.user)
		return render (request, 'crue_traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'editar',
			'registro': registro,
			'mes': registro.mes,
		})

	def post (self, request, pk):
		"""Valida y guarda los cambios; retorna tabla actualizada o modal con errores."""
		registro = get_object_or_404 (Traslado, pk=pk)
		formulario = FormularioTraslado (request.POST, instance=registro, usuario=request.user)
		if formulario.is_valid ():
			try:
				formulario.save ()
			except ValidationError as e:
				formulario.add_error (None, e)
				return render (request, 'crue_traslados/partials/modal_form.html', {
					'formulario': formulario,
					'accion': 'editar',
					'registro': registro,
					'mes': registro.mes,
				})

			mes = registro.mes
			contexto = _obtenerContextoTabla (mes, datetime.date.today ().year)
			respuesta = render (request, 'crue_traslados/partials/table.html', contexto)
			respuesta ['HX-Trigger'] = 'cerrarModal'
			return respuesta

		return render (request, 'crue_traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'editar',
			'registro': registro,
			'mes': registro.mes,
		})


# ─── Vista HTMX: clonar traslado ──────────────────────────────────────────────

class VistaClonarTrasladoHTMX (CrueRequiredMixin, View):
	"""Crea una copia del registro con fechas/horas reiniciadas y abre el modal de creación."""

	def get (self, request, pk):
		"""Retorna el modal con datos clonados del registro original."""
		registro = get_object_or_404 (Traslado, pk=pk)

		hoyISO = datetime.date.today ().isoformat ()
		horaActual = datetime.datetime.now ().strftime ('%H:%M')

		# Construir initial con los campos copiados del registro original
		initial = {
			'fecha_reporte': [hoyISO, horaActual],
			'fecha_egreso': [hoyISO, ''],
			'fecha_ingreso': [hoyISO, ''],
			'nombre_paciente': registro.nombre_paciente,
			'documento': registro.documento,
			'servicio': registro.servicio,
			'quien_reporta': registro.quien_reporta,
			'destino': registro.destino,
			'procedimiento': registro.procedimiento,
			'medico': registro.medico,
			'aux_enfermeria': registro.aux_enfermeria,
			'conductor': registro.conductor,
			# radio_operador se asigna desde el usuario actual (no se copia)
			'ambulancia': registro.ambulancia,
			'observacion': registro.observacion,
		}

		formulario = FormularioTraslado (initial=initial, usuario=request.user)
		return render (request, 'crue_traslados/partials/modal_form.html', {
			'formulario': formulario,
			'accion': 'crear',
			'mes': datetime.date.today ().month,
		})


# ─── Helper: verificar permiso de eliminación ────────────────────────────────

def _puedeEliminar (usuario, registro):
	"""Retorna True si el usuario puede eliminar el registro (staff o dueño por radio_operador)."""
	if usuario.is_staff:
		return True
	return registro.radio_operador.strip ().lower () == usuario.username.strip ().lower ()


# ─── Vista HTMX: confirmar eliminación ───────────────────────────────────────

class VistaConfirmarEliminarHTMX (CrueRequiredMixin, View):
	"""Muestra el partial de confirmación de eliminación."""

	def get (self, request, pk):
		"""Retorna el partial de confirmación; 403 si no tiene permiso; 404 si no existe."""
		registro = get_object_or_404 (Traslado, pk=pk)
		if not _puedeEliminar (request.user, registro):
			return HttpResponse ('No tiene permiso para eliminar este registro.', status=403)
		return render (request, 'crue_traslados/partials/confirmar_eliminar.html', {
			'registro': registro,
		})


# ─── Vista HTMX: eliminar traslado ────────────────────────────────────────────

class VistaEliminarTrasladoHTMX (CrueRequiredMixin, View):
	"""Elimina un registro y retorna la tabla actualizada."""

	def delete (self, request, pk):
		"""Elimina el registro; 403 si no tiene permiso; 404 si no existe."""
		registro = get_object_or_404 (Traslado, pk=pk)
		if not _puedeEliminar (request.user, registro):
			return HttpResponse ('No tiene permiso para eliminar este registro.', status=403)
		mes = registro.mes
		registro.delete ()

		contexto = _obtenerContextoTabla (mes, datetime.date.today ().year)
		respuesta = render (request, 'crue_traslados/partials/table.html', contexto)
		respuesta ['HX-Trigger'] = 'cerrarModal'
		return respuesta


# ─── Vista: reporte Excel ─────────────────────────────────────────────────────

class VistaReporteExcel (CrueRequiredMixin, View):
	"""Genera y descarga el reporte Excel de traslados filtrados por mes y búsqueda."""

	def get (self, request):
		"""Lee los parámetros de filtro, genera el Excel y retorna la respuesta de descarga."""
		import calendar
		from django.utils import timezone as tz
		mes, anio, busqueda = _obtenerFiltros (request)

		diasEnMes = calendar.monthrange (anio, mes) [1]
		fechaDesde = tz.make_aware (datetime.datetime (anio, mes, 1, 0, 0, 0))
		fechaHasta = tz.make_aware (datetime.datetime (anio, mes, diasEnMes, 23, 59, 59))

		queryset = Traslado.objects.filter (
			fecha_reporte__gte=fechaDesde,
			fecha_reporte__lte=fechaHasta,
		).order_by ('fecha_reporte')

		if busqueda:
			queryset = queryset.filter (
				Q (documento__icontains=busqueda) | Q (nombre_paciente__icontains=busqueda)
			)

		try:
			bytesArchivo, nombreArchivo = generarExcel (queryset, mes)
		except Exception as exc:
			logger.exception ('Error al generar el reporte Excel: %s', exc)
			return render (request, 'crue_traslados/error_reporte.html', {
				'mensaje': 'Ocurrió un error al generar el reporte Excel. Por favor, intente nuevamente.',
			}, status=500)

		respuesta = HttpResponse (
			bytesArchivo,
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)
		respuesta ['Content-Disposition'] = f'attachment; filename="{nombreArchivo}"'
		return respuesta


# ─── Vista: cambiar contraseña propia ────────────────────────────────────────

# ─── Vista: importar desde Excel ──────────────────────────────────────────────

class VistaImportarExcel (CrueRequiredMixin, View):
	"""Importa registros de traslados desde un archivo Excel (solo staff)."""

	def get (self, request):
		"""Muestra el formulario de carga de archivo."""
		if not _esStaff (request.user):
			return HttpResponse ('No tiene permiso para acceder a esta función.', status=403)
		return render (request, 'crue_traslados/importar_excel.html', {'paso': 'subir'})

	def post (self, request):
		"""Procesa la carga del archivo (paso 1) o ejecuta la importación (paso 2)."""
		if not _esStaff (request.user):
			return HttpResponse ('No tiene permiso para acceder a esta función.', status=403)

		if 'archivo' in request.FILES:
			return self._procesarArchivo (request)
		elif 'hoja' in request.POST:
			return self._ejecutarImportacion (request)

		return redirect ('crue_traslados:importar-excel')

	def _procesarArchivo (self, request):
		"""Guarda el archivo temporal y muestra las hojas disponibles."""
		import os
		import tempfile

		archivo = request.FILES ['archivo']
		tmpDir = tempfile.gettempdir ()
		tmpPath = os.path.join (tmpDir, f'import_{request.user.pk}.xlsx')

		with open (tmpPath, 'wb') as f:
			for chunk in archivo.chunks ():
				f.write (chunk)

		from .utils import obtenerHojasExcel
		hojas = obtenerHojasExcel (tmpPath)

		return render (request, 'crue_traslados/importar_excel.html', {
			'paso': 'seleccionar_hoja',
			'hojas': hojas,
			'nombreArchivo': archivo.name,
		})

	def _ejecutarImportacion (self, request):
		"""Lee el archivo temporal, importa los datos y muestra resultados."""
		import os
		import tempfile

		hoja = request.POST ['hoja']
		tmpDir = tempfile.gettempdir ()
		tmpPath = os.path.join (tmpDir, f'import_{request.user.pk}.xlsx')

		if not os.path.exists (tmpPath):
			return render (request, 'crue_traslados/importar_excel.html', {
				'paso': 'subir',
				'error': 'El archivo temporal expiró. Por favor, cargue el archivo nuevamente.',
			})

		from .utils import import_traslados_from_excel
		try:
			insertados, omitidos = import_traslados_from_excel (file_path=tmpPath, sheet_name=hoja)
		except Exception as exc:
			logger.exception ('Error al importar desde Excel: %s', exc)
			return render (request, 'crue_traslados/importar_excel.html', {
				'paso': 'subir',
				'error': f'Error al importar: {exc}',
			})
		finally:
			if os.path.exists (tmpPath):
				os.remove (tmpPath)

		return render (request, 'crue_traslados/importar_excel.html', {
			'paso': 'resultado',
			'insertados': insertados,
			'omitidos': omitidos,
			'hoja': hoja,
		})


# ─── Vista: cambiar contraseña propia ────────────────────────────────────────

class VistaCambiarContrasena (CrueRequiredMixin, View):
	"""Muestra el formulario de cambio de contraseña (GET) y procesa el cambio (POST)."""

	def get (self, request):
		"""Renderiza el formulario de cambio de contraseña."""
		from .forms import FormularioCambiarContrasena
		formulario = FormularioCambiarContrasena ()
		return render (request, 'crue_traslados/cambiar_contrasena.html', {
			'formulario': formulario,
		})

	def post (self, request):
		"""Valida y actualiza la contraseña del usuario autenticado."""
		from .forms import FormularioCambiarContrasena
		formulario = FormularioCambiarContrasena (request.POST)
		if formulario.is_valid ():
			contrasenaActual = formulario.cleaned_data ['contrasena_actual']
			nuevaContrasena = formulario.cleaned_data ['nueva_contrasena']

			if not request.user.check_password (contrasenaActual):
				formulario.add_error ('contrasena_actual', 'La contraseña actual es incorrecta.')
				return render (request, 'crue_traslados/cambiar_contrasena.html', {
					'formulario': formulario,
				})

			request.user.set_password (nuevaContrasena)
			request.user.save ()

			from django.contrib.auth import update_session_auth_hash
			update_session_auth_hash (request, request.user)

			return render (request, 'crue_traslados/cambiar_contrasena.html', {
				'formulario': FormularioCambiarContrasena (),
				'exito': True,
			})

		return render (request, 'crue_traslados/cambiar_contrasena.html', {
			'formulario': formulario,
		})
