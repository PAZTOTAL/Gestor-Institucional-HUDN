"""
Vistas de la aplicación CRUE Remisiones Pacientes.

Todas las vistas requieren pertenencia al grupo 'crue_remisiones'
mediante el decorador @crue_required.
"""

from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date

from .decorators import crue_required
from .forms import (
	CambiarPasswordForm,
	ImportarExcelForm,
	LoginForm,
	RemisionForm,
)
from .models import Remision
from .services import (
	calcular_oportunidad,
	es_registro_editable,
	exportar_a_excel,
	importar_desde_excel,
	obtener_remisiones,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MESES_ES = [
	(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
	(5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
	(9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


# ---------------------------------------------------------------------------
# Vistas de autenticación
# ---------------------------------------------------------------------------

def login_view(request):
	"""GET/POST /login/ — Autenticación de usuario."""

	if request.user.is_authenticated:
		return redirect(settings.LOGIN_REDIRECT_URL)

	form = LoginForm(request.POST or None)
	error = None

	if request.method == "POST" and form.is_valid():
		username = form.cleaned_data["username"]
		password = form.cleaned_data["password"]

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)

			next_url = request.GET.get("next")
			if next_url:
				return redirect(next_url)

			return redirect(settings.LOGIN_REDIRECT_URL)

		error = "Usuario o contraseña incorrectos."

	return render(
		request,
		"crueremisiones/login.html",
		{
			"form": form,
			"error": error,
		},
	)

#def login_view(request):
#	"""GET/POST /login/ — Autenticación de usuario."""
#	if request.user.is_authenticated:
#		#return redirect('crueremisiones:main')
#		return redirect(settings.LOGIN_REDIRECT_URL)
#
#	form = LoginForm(request.POST or None)
#	error = None
#
#	if request.method == 'POST' and form.is_valid():
#		username = form.cleaned_data['username']
#		password = form.cleaned_data['password']
#		user = authenticate(request, username=username, password=password)
#		if user is not None:
#			login(request, user)
#			return redirect(settings.LOGIN_REDIRECT_URL)
#			#return redirect('crueremisiones:main')
#		else:
#			error = 'Usuario o contraseña incorrectos.'
#
#	return render(request, 'crueremisiones/login.html', {'form': form, 'error': error})


def logout_view(request):
	"""POST /logout/ — Cierre de sesión."""
	logout(request)
	#return redirect('/login/')
	return redirect(settings.LOGOUT_REDIRECT_URL)

# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

@crue_required
def main_view(request):
	"""GET / — Vista principal con tabla de remisiones."""
	#hoy = timezone.localdate()
	hoy = date.today ()

	# Parámetros de filtro desde GET
	filtro = request.GET.get('filtro', 'mes')
	mes = request.GET.get('mes')
	anio = request.GET.get('anio')
	doc = request.GET.get('doc', '')
	page = request.GET.get('page', 1)
	orden = request.GET.get('orden', 'desc')  # 'desc' = newest first (default)

	# Valores por defecto para filtro mes
	try:
		mes = int(mes)
	except (TypeError, ValueError):
		mes = hoy.month

	try:
		anio = int(anio)
	except (TypeError, ValueError):
		anio = hoy.year

	# Pagination: default ON for past months, OFF for current month
	es_mes_actual = (filtro == 'mes' and mes == hoy.month and anio == hoy.year)
	paginado_param = request.GET.get('paginado', None)
	if paginado_param is not None:
		# User explicitly set the checkbox
		paginado = (paginado_param == 'True')
	else:
		# Default: paginated for past months, not for current month
		if es_mes_actual:
			paginado = False
		else:
			paginado = True

	# Construir kwargs para el servicio
	kwargs = {'orden': orden}
	if filtro == 'mes':
		kwargs.update({'mes': mes, 'anio': anio})
	elif filtro == 'documento':
		kwargs.update({'doc': doc})

	qs = obtener_remisiones(filtro, **kwargs)

	# Paginación
	page_obj = None
	usar_paginacion = paginado

	if usar_paginacion:
		paginator = Paginator(qs, 15)
		page_obj = paginator.get_page(page)
		remisiones_lista = page_obj.object_list
	else:
		remisiones_lista = qs

	# Anotar cada remisión con oportunidad
	remisiones_con_oportunidad = []
	for remision in remisiones_lista:
		remision.oportunidad = calcular_oportunidad(remision.fecha, remision.fecha_res)
		remisiones_con_oportunidad.append(remision)

	# Fecha de hoy formateada en español
	fecha_hoy = f"{hoy.day} de {MESES_ES[hoy.month - 1][1]} de {hoy.year}"

	context = {
		'remisiones': remisiones_con_oportunidad,
		'page_obj': page_obj,
		'filtro': filtro,
		'mes_actual': mes,
		'anio_actual': anio,
		'meses': MESES_ES,
		'fecha_hoy': fecha_hoy,
		'paginado': paginado,
		'doc': doc,
		'orden': orden,
		'mes_hoy': hoy.month,
		'anio_hoy': hoy.year,
		'usuario_nombre_completo': request.user.get_full_name(),
	}
	return render(request, 'crueremisiones/main.html', context)


# ---------------------------------------------------------------------------
# Vistas CRUD
# ---------------------------------------------------------------------------

@crue_required
def remision_create(request):
	"""POST /remisiones/nueva/ — Crear remisión (AJAX)."""
	form = RemisionForm(request.POST)
	if form.is_valid():
		remision = form.save(commit=False)
		remision.created_by = request.user
		# radio_operador is always set to the creator's full name
		remision.radio_operador = request.user.get_full_name() or request.user.username
		remision.save()
		return JsonResponse({'ok': True, 'id': remision.id})
	return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def remision_detail(request, pk):
	"""GET /remisiones/<pk>/detalle/ — Detalle JSON para modal (AJAX)."""
	remision = get_object_or_404(Remision, pk=pk)
	oportunidad = calcular_oportunidad(remision.fecha, remision.fecha_res)

	def fmt_dt(dt):
		"""Formatea datetime para inputs datetime-local."""
		if dt is None:
			return ''
		return dt.strftime('%Y-%m-%dT%H:%M')

	data = {
		'id': remision.id,
		'fecha': fmt_dt(remision.fecha),
		'nombre': remision.nombre,
		'tipo_doc': remision.tipo_doc,
		'doc': remision.doc,
		'sexo': remision.sexo,
		'edad': remision.edad,
		'especialidad': remision.especialidad,
		'gest': remision.gest,
		'diagnostico': remision.diagnostico,
		'ta': remision.ta,
		'fc': remision.fc,
		'fr': remision.fr,
		'tm': remision.tm,
		'spo2': remision.spo2,
		'glasg': remision.glasg,
		'eps': remision.eps,
		'institucion_reporta': remision.institucion_reporta,
		'municipio': remision.municipio,
		'medico_refiere': remision.medico_refiere,
		'medico_hudn': remision.medico_hudn,
		'radio_operador': remision.radio_operador,
		'observacion': remision.observacion,
		'aceptado': remision.aceptado,
		'fecha_res': fmt_dt(remision.fecha_res),
		'oportunidad': oportunidad,
		'es_editable': remision.es_editable,
		'es_propio': remision.created_by == request.user,
	}
	print (f"+++ {data=}")
	return JsonResponse(data)


@crue_required
def remision_update(request, pk):
	"""POST /remisiones/<pk>/editar/ — Editar remisión (AJAX)."""
	remision = get_object_or_404(Remision, pk=pk)

	if not es_registro_editable(remision):
		return JsonResponse(
			{'ok': False, 'error': 'Registro histórico: no se puede modificar.'},
			status=403,
		)

	# Solo el propietario del registro puede editarlo
	if remision.created_by != request.user:
		return JsonResponse(
			{'ok': False, 'error': 'Solo puede modificar sus propios registros.'},
			status=403,
		)

	form = RemisionForm(request.POST, instance=remision)
	if form.is_valid():
		# Preserve original radio_operador — it's read-only
		form.instance.radio_operador = remision.radio_operador
		form.save()
		return JsonResponse({'ok': True})
	return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def remision_delete(request, pk):
	"""POST /remisiones/<pk>/eliminar/ — Eliminar remisión (AJAX)."""
	remision = get_object_or_404(Remision, pk=pk)

	if not es_registro_editable(remision):
		return JsonResponse(
			{'ok': False, 'error': 'Registro histórico: no se puede eliminar.'},
			status=403,
		)

	# Solo el propietario del registro puede eliminarlo
	if remision.created_by != request.user:
		return JsonResponse(
			{'ok': False, 'error': 'Solo puede eliminar sus propios registros.'},
			status=403,
		)

	remision.delete()
	return JsonResponse({'ok': True})


@crue_required
def exportar_excel(request):
	"""GET /exportar/excel/ — Exportar remisiones a Excel."""
	#hoy = timezone.localdate()
	hoy = date.today ()

	filtro = request.GET.get('filtro', 'mes')
	mes = request.GET.get('mes')
	anio = request.GET.get('anio')
	doc = request.GET.get('doc', '')

	try:
		mes = int(mes)
	except (TypeError, ValueError):
		mes = hoy.month

	try:
		anio = int(anio)
	except (TypeError, ValueError):
		anio = hoy.year

	kwargs = {}
	if filtro == 'mes':
		kwargs = {'mes': mes, 'anio': anio}
	elif filtro == 'documento':
		kwargs = {'doc': doc}

	qs = obtener_remisiones(filtro, **kwargs)

	if not qs.exists():
		return JsonResponse(
			{'ok': False, 'error': 'No hay registros para el período seleccionado.'},
			status=400,
		)

	buffer = exportar_a_excel(qs)
	filename = f"remisiones_{hoy.strftime('%Y-%m-%d')}.xlsx"
	response = HttpResponse(
		buffer.read(),
		content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	)
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response


@crue_required
def importar_excel(request):
	"""POST /importar/excel/ — Importar remisiones desde Excel."""
	import tempfile
	import os
	form = ImportarExcelForm(request.POST, request.FILES)
	if form.is_valid():
		archivo = form.cleaned_data['archivo']
		sheet_name = request.POST.get('sheet_name', None)
		# Save to temp file for excelToDataframe (needs a path)
		with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
			for chunk in archivo.chunks():
				tmp.write(chunk)
			temp_path = tmp.name
		try:
			resultado = importar_desde_excel(temp_path, request.user, sheet_name=sheet_name)
		finally:
			if os.path.exists(temp_path):
				os.unlink(temp_path)
		status_code = 200 if resultado.get('ok') else 400
		return JsonResponse(resultado, status=status_code)
	return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def importar_excel_hojas(request):
	"""POST /importar/excel/hojas/ — Retorna la lista de hojas del archivo Excel."""
	import tempfile
	import os
	import openpyxl

	if 'archivo' not in request.FILES:
		return JsonResponse({'ok': False, 'error': 'No se envió archivo.'}, status=400)

	archivo = request.FILES['archivo']
	with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
		for chunk in archivo.chunks():
			tmp.write(chunk)
		temp_path = tmp.name

	try:
		wb = openpyxl.load_workbook(temp_path, read_only=True, data_only=True)
		hojas = wb.sheetnames
		wb.close()
		return JsonResponse({'ok': True, 'hojas': hojas})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': f'No se pudo leer el archivo: {e}'}, status=400)
	finally:
		if os.path.exists(temp_path):
			os.unlink(temp_path)


# ---------------------------------------------------------------------------
# Vistas de gestión de usuarios
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cambio de contraseña propia
# ---------------------------------------------------------------------------

@crue_required
def cambiar_password_view(request):
	"""GET/POST /cambiar-password/ — Cambio de contraseña propia."""
	form = CambiarPasswordForm(request.POST or None)
	error = None
	exito = None

	if request.method == 'POST' and form.is_valid():
		password_actual = form.cleaned_data['password_actual']
		password_nueva = form.cleaned_data['password_nueva']

		if not request.user.check_password(password_actual):
			error = 'La contraseña actual es incorrecta.'
		else:
			request.user.set_password(password_nueva)
			request.user.save()
			update_session_auth_hash(request, request.user)
			exito = 'Contraseña cambiada correctamente.'
			form = CambiarPasswordForm()

	return render(
		request,
		'crueremisiones/cambiar_password.html',
		{'form': form, 'error': error, 'exito': exito},
	)
