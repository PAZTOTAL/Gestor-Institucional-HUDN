"""
Vistas de la aplicación CRUE Remisiones Pacientes.

Todas las vistas (excepto login, logout y recuperar_password) requieren
autenticación mediante el decorador @login_required.
"""

from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AdminCambiarPasswordForm,
    CambiarPasswordForm,
    ImportarExcelForm,
    LoginForm,
    RecuperarPasswordForm,
    RemisionForm,
    UsuarioEditForm,
    UsuarioForm,
)
from .models import Remision, UsuarioCrue
from .services import (
    calcular_oportunidad,
    enviar_email_recuperacion,
    es_registro_editable,
    exportar_a_excel,
    generar_password_temporal,
    importar_desde_excel,
    importar_desde_excel_v2,
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
        return redirect('/')

    form = LoginForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error = 'Usuario o contraseña incorrectos.'

    return render(request, 'remisiones/login.html', {'form': form, 'error': error})


def logout_view(request):
    """POST /logout/ — Cierre de sesión."""
    logout(request)
    return redirect('/login/')


def recuperar_password_view(request):
    """GET/POST /recuperar-password/ — Recuperación de contraseña."""
    form = RecuperarPasswordForm(request.POST or None)
    mensaje = None

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        try:
            user = UsuarioCrue.objects.get(username=username)
            password_temp = generar_password_temporal()
            user.set_password(password_temp)
            user.save()
            enviar_email_recuperacion(user, password_temp)
        except UsuarioCrue.DoesNotExist:
            pass  # No revelar si el usuario existe o no (seguridad)
        # Siempre mostrar mensaje genérico
        mensaje = (
            'Si el usuario existe, se ha enviado una contraseña temporal '
            'al correo registrado.'
        )

    return render(
        request,
        'remisiones/recuperar_password.html',
        {'form': form, 'mensaje': mensaje},
    )


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

@login_required
def main_view(request):
    """GET / — Vista principal con tabla de remisiones."""
    hoy = timezone.localdate()

    # Parámetros de filtro desde GET
    filtro = request.GET.get('filtro', 'mes')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    doc = request.GET.get('doc', '')
    paginado = request.GET.get('paginado', '') == 'True'
    page = request.GET.get('page', 1)

    # Valores por defecto para filtro mes
    try:
        mes = int(mes)
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(anio)
    except (TypeError, ValueError):
        anio = hoy.year

    # Construir kwargs para el servicio
    kwargs = {}
    if filtro == 'mes':
        kwargs = {'mes': mes, 'anio': anio}
    elif filtro == 'rango':
        kwargs = {'desde': desde, 'hasta': hasta}
    elif filtro == 'documento':
        kwargs = {'doc': doc}

    qs = obtener_remisiones(filtro, **kwargs)

    # Paginación
    page_obj = None
    usar_paginacion = (filtro == 'rango') or (filtro == 'mes' and paginado)

    if usar_paginacion:
        paginator = Paginator(qs, 20)
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
        'desde': desde,
        'hasta': hasta,
        'doc': doc,
        'usuario_nombre_completo': request.user.get_full_name(),
    }
    return render(request, 'remisiones/main.html', context)


# ---------------------------------------------------------------------------
# Vistas CRUD
# ---------------------------------------------------------------------------

@login_required
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


@login_required
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
        'especialidad': remision.especialidad,
        'edad': remision.edad,
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
    return JsonResponse(data)


@login_required
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


@login_required
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


@login_required
def exportar_excel(request):
    """GET /exportar/excel/ — Exportar remisiones a Excel."""
    hoy = timezone.localdate()

    filtro = request.GET.get('filtro', 'mes')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
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
    elif filtro == 'rango':
        kwargs = {'desde': desde, 'hasta': hasta}
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


@login_required
def importar_excel(request):
    """POST /importar/excel/ — Importar remisiones desde Excel."""
    import tempfile
    import os
    form = ImportarExcelForm(request.POST, request.FILES)
    if form.is_valid():
        archivo = form.cleaned_data['archivo']
        # Save to temp file for excelToDataframe (needs a path)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            temp_path = tmp.name
        try:
            resultado = importar_desde_excel_v2(temp_path, request.user)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        status_code = 200 if resultado.get('ok') else 400
        return JsonResponse(resultado, status=status_code)
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


# ---------------------------------------------------------------------------
# Vistas de gestión de usuarios
# ---------------------------------------------------------------------------

@login_required
def usuarios_view(request):
    """GET/POST /usuarios/ — Gestión de usuarios (solo DIRECTOR)."""
    if request.user.rol != 'DIRECTOR':
        messages.error(request, 'No tiene permisos para acceder a esta sección.')
        return redirect('/')

    usuarios = UsuarioCrue.objects.all().order_by('username')
    form = UsuarioForm(request.POST or None)
    error = None

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            user = UsuarioCrue.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
            )
            user.rol = data['rol']
            user.save()
            messages.success(request, f'Usuario "{user.username}" creado correctamente.')
            return redirect('/usuarios/')
        else:
            error = 'Por favor corrija los errores del formulario.'

    return render(
        request,
        'remisiones/usuarios.html',
        {'usuarios': usuarios, 'form': form, 'error': error},
    )


@login_required
def usuario_delete(request, pk):
    """POST /usuarios/<pk>/eliminar/ — Eliminar usuario (solo DIRECTOR)."""
    if request.user.rol != 'DIRECTOR':
        return JsonResponse(
            {'ok': False, 'error': 'No tiene permisos para esta acción.'},
            status=403,
        )

    if pk == request.user.pk:
        return JsonResponse(
            {'ok': False, 'error': 'No puede eliminar su propio usuario.'},
            status=400,
        )

    user = get_object_or_404(UsuarioCrue, pk=pk)
    user.delete()
    return JsonResponse({'ok': True})


@login_required
def usuario_edit(request, pk):
    """GET/POST /usuarios/<pk>/editar/ — Editar usuario (solo DIRECTOR)."""
    if request.user.rol != 'DIRECTOR':
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('/')

    user = get_object_or_404(UsuarioCrue, pk=pk)

    if request.method == 'POST':
        form = UsuarioEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.rol = data['rol']
            user.save()
            messages.success(request, f'Usuario "{user.username}" actualizado correctamente.')
            return redirect('/usuarios/')
    else:
        form = UsuarioEditForm(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'rol': user.rol,
        })

    return render(request, 'remisiones/usuario_editar.html', {
        'form': form,
        'usuario_editado': user,
    })


@login_required
def usuario_cambiar_password(request, pk):
    """GET/POST /usuarios/<pk>/cambiar-password/ — Cambiar contraseña de usuario (solo DIRECTOR)."""
    if request.user.rol != 'DIRECTOR':
        messages.error(request, 'No tiene permisos para esta acción.')
        return redirect('/')

    user = get_object_or_404(UsuarioCrue, pk=pk)

    if request.method == 'POST':
        form = AdminCambiarPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password_nueva'])
            user.save()
            messages.success(request, f'Contraseña de "{user.username}" cambiada correctamente.')
            return redirect('/usuarios/')
    else:
        form = AdminCambiarPasswordForm()

    return render(request, 'remisiones/usuario_cambiar_password.html', {
        'form': form,
        'usuario_editado': user,
    })


@login_required
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
            form = CambiarPasswordForm()  # Limpiar formulario

    return render(
        request,
        'remisiones/cambiar_password.html',
        {'form': form, 'error': error, 'exito': exito},
    )
