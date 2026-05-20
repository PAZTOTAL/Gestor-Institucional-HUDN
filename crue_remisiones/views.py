from datetime import date

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

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

MESES_ES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


def login_view(request):
    if request.user.is_authenticated:
        return redirect('crue_remisiones:main')

    form = LoginForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('crue_remisiones:main')
        error = 'Usuario o contraseña incorrectos.'

    return render(request, 'crue_remisiones/login.html', {'form': form, 'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@crue_required
def main_view(request):
    hoy = date.today()

    filtro = request.GET.get('filtro', 'mes')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    doc = request.GET.get('doc', '')
    page = request.GET.get('page', 1)
    orden = request.GET.get('orden', 'desc')

    try:
        mes = int(mes)
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(anio)
    except (TypeError, ValueError):
        anio = hoy.year

    es_mes_actual = (filtro == 'mes' and mes == hoy.month and anio == hoy.year)
    paginado_param = request.GET.get('paginado', None)
    if paginado_param is not None:
        paginado = (paginado_param == 'True')
    else:
        paginado = True

    kwargs = {'orden': orden}
    if filtro == 'mes':
        kwargs.update({'mes': mes, 'anio': anio})
    elif filtro == 'documento':
        kwargs.update({'doc': doc})

    qs = obtener_remisiones(filtro, **kwargs)

    page_obj = None
    if paginado:
        paginator = Paginator(qs, 15)
        page_obj = paginator.get_page(page)
        remisiones_lista = page_obj.object_list
    else:
        remisiones_lista = qs

    remisiones_con_oportunidad = []
    for remision in remisiones_lista:
        remision.oportunidad = calcular_oportunidad(remision.fecha, remision.fecha_res)
        remisiones_con_oportunidad.append(remision)

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
        'es_admin': request.user.is_staff or request.user.is_superuser,
        'usuario_nombre_completo': request.user.get_full_name(),
    }
    return render(request, 'crue_remisiones/main.html', context)


@crue_required
def remision_create(request):
    form = RemisionForm(request.POST)
    if form.is_valid():
        remision = form.save(commit=False)
        remision.created_by = request.user
        remision.radio_operador = request.user.get_full_name() or request.user.username
        remision.save()
        return JsonResponse({'ok': True, 'id': remision.id})
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def remision_detail(request, pk):
    remision = get_object_or_404(Remision, pk=pk)
    oportunidad = calcular_oportunidad(remision.fecha, remision.fecha_res)

    def fmt_dt(dt):
        if dt is None:
            return ''
        # If timezone-aware, convert to local time before formatting
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            import zoneinfo
            local_tz = zoneinfo.ZoneInfo('America/Bogota')
            dt = dt.astimezone(local_tz)
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
        'es_admin': request.user.is_staff or request.user.is_superuser,
    }
    return JsonResponse(data)


@crue_required
def remision_update(request, pk):
    remision = get_object_or_404(Remision, pk=pk)
    is_admin = request.user.is_staff or request.user.is_superuser

    if not is_admin:
        if not es_registro_editable(remision):
            return JsonResponse({'ok': False, 'error': 'Registro histórico: no se puede modificar.'}, status=403)
        if remision.created_by != request.user:
            return JsonResponse({'ok': False, 'error': 'Solo puede modificar sus propios registros.'}, status=403)

    form = RemisionForm(request.POST, instance=remision)
    if form.is_valid():
        form.instance.radio_operador = remision.radio_operador
        form.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def remision_delete(request, pk):
    remision = get_object_or_404(Remision, pk=pk)
    is_admin = request.user.is_staff or request.user.is_superuser

    if not is_admin:
        if not es_registro_editable(remision):
            return JsonResponse({'ok': False, 'error': 'Registro histórico: no se puede eliminar.'}, status=403)
        if remision.created_by != request.user:
            return JsonResponse({'ok': False, 'error': 'Solo puede eliminar sus propios registros.'}, status=403)

    remision.delete()
    return JsonResponse({'ok': True})


@crue_required
def exportar_excel(request):
    hoy = date.today()

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
        return JsonResponse({'ok': False, 'error': 'No hay registros para el período seleccionado.'}, status=400)

    # Force ascending order for the report (first to last day)
    qs = qs.order_by('fecha')

    buffer = exportar_a_excel(qs)

    # Filename: reporte_remisiones_YYYY_MMMM_DD.xlsx
    meses_es = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    nombre_mes = meses_es[hoy.month - 1]
    filename = f"reporte_remisiones_{hoy.year}_{nombre_mes}_{hoy.day:02d}.xlsx"
    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@crue_required
def importar_excel(request):
    import tempfile
    import os
    form = ImportarExcelForm(request.POST, request.FILES)
    if form.is_valid():
        archivo = form.cleaned_data['archivo']
        sheet_name = request.POST.get('sheet_name', None)
        tipo_formato = request.POST.get('tipoFormatoExcel', 'FRALG-062')
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            temp_path = tmp.name
        try:
            resultado = importar_desde_excel(temp_path, request.user, tipoFormatoExcel=tipo_formato, sheet_name=sheet_name)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        status_code = 200 if resultado.get('ok') else 400
        return JsonResponse(resultado, status=status_code)
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@crue_required
def importar_excel_hojas(request):
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


@crue_required
def cambiar_password_view(request):
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

    return render(request, 'crue_remisiones/cambiar_password.html', {'form': form, 'error': error, 'exito': exito})
