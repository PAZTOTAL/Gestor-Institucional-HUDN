import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from ..models import ListaBlancaAdmin, EncabezadoConfig, CoordinadorAreaGmail, FirmaAPC
from ..auth import create_token, decode_token


def _get_admin(username: str):
    try:
        return ListaBlancaAdmin.objects.get(usunombre=username, activo=True)
    except ListaBlancaAdmin.DoesNotExist:
        return None


def _get_coordinador(username: str):
    return CoordinadorAreaGmail.objects.filter(usuario_dinamica=username).first()


def _make_avatar(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else 'U'


def _get_encabezado():
    enc, _ = EncabezadoConfig.objects.get_or_create(
        pk=1,
        defaults={
            'titulo': 'ASIGNACIÓN DE PERMISOS Y CLAVES',
            'codigo': 'FRSGI-002',
            'version': '06',
            'fecha_elaboracion': '05 DE JUNIO DE 2014',
            'fecha_actualizacion': '22 DE SEPTIEMBRE DE 2023',
            'hoja': '1 DE 1',
        }
    )
    return enc


@login_required
def apc_landing(request: HttpRequest):
    lb = _get_admin(request.user.username)
    coord = _get_coordinador(request.user.username)
    fn = (request.user.first_name or '').strip()
    ln = (request.user.last_name or '').strip()
    nombre = f"{fn} {ln}".strip() or request.user.username
    avatar = _make_avatar(nombre)

    return render(request, 'asignacion_permisos/landing.html', {
        'nombre': nombre,
        'avatar': avatar,
        'es_admin': lb is not None,
        'es_coordinador': coord is not None,
    })


@login_required
def apc_panel(request: HttpRequest):
    lb = _get_admin(request.user.username)
    if lb is None:
        return redirect('asignacion_permisos:apc_landing')

    fn = (request.user.first_name or '').strip()
    ln = (request.user.last_name or '').strip()
    nombre = f"{fn} {ln}".strip() or request.user.username
    avatar = _make_avatar(nombre)

    token = create_token({
        'usunombre': lb.usunombre,
        'usuemail': lb.usuemail,
        'nombre': nombre,
        'rol': 'apc_admin',
    })

    user_json = json.dumps({
        'usunombre': lb.usunombre,
        'nombre': nombre,
        'rol': 'apc_admin',
        'avatar': avatar,
    }, ensure_ascii=False)

    return render(request, 'asignacion_permisos/index.html', {
        'apc_token': token,
        'apc_user_json': user_json,
        'nombre': nombre,
        'avatar': avatar,
    })


def apc_solicitud_publica(request: HttpRequest):
    prefill = {}
    if request.user.is_authenticated:
        fn = (request.user.first_name or '').strip()
        ln = (request.user.last_name or '').strip()
        prefill['nombre'] = f"{fn} {ln}".strip()
        prefill['username'] = request.user.username

    return render(request, 'asignacion_permisos/solicitud_publica.html', {
        'prefill_json': json.dumps(prefill, ensure_ascii=False),
        'user_autenticado': request.user.is_authenticated,
    })


def apc_firmar(request: HttpRequest):
    token = request.GET.get('token', '')
    error = None
    firma_data = None

    if token:
        try:
            decode_token(token)
        except ValueError as e:
            error = str(e)
    else:
        error = 'Token no proporcionado'

    enc = _get_encabezado()
    encabezado = {
        'titulo': enc.titulo,
        'codigo': enc.codigo,
        'version': enc.version,
        'fecha_elaboracion': enc.fecha_elaboracion,
        'fecha_actualizacion': enc.fecha_actualizacion,
        'hoja': enc.hoja,
    }

    return render(request, 'asignacion_permisos/firmar.html', {
        'token': token,
        'error': error,
        'encabezado_json': json.dumps(encabezado, ensure_ascii=False),
    })


@login_required
def apc_coordinador(request: HttpRequest):
    coord = _get_coordinador(request.user.username)
    if coord is None:
        return redirect('asignacion_permisos:apc_landing')

    fn = (request.user.first_name or '').strip()
    ln = (request.user.last_name or '').strip()
    nombre = f"{fn} {ln}".strip() or request.user.username
    avatar = _make_avatar(nombre)

    pendientes = list(
        FirmaAPC.objects
        .filter(nombre_firmante=coord.nombre, firmado=False)
        .select_related('solicitud')
        .prefetch_related('solicitud__permisos_solicitados')
        .order_by('-solicitud__fecha_diligenciamiento')
    )
    firmadas = list(
        FirmaAPC.objects
        .filter(nombre_firmante=coord.nombre, firmado=True)
        .select_related('solicitud')
        .order_by('-fecha_firma')[:20]
    )

    return render(request, 'asignacion_permisos/coordinador.html', {
        'nombre': nombre,
        'avatar': avatar,
        'coord': coord,
        'pendientes': pendientes,
        'firmadas': firmadas,
    })


@login_required
@require_POST
def apc_coordinador_guardar_firma(request: HttpRequest):
    coord = _get_coordinador(request.user.username)
    if coord is None:
        return JsonResponse({'detail': 'No autorizado'}, status=403)
    try:
        body = json.loads(request.body)
        firma_imagen = body.get('firma_imagen', '').strip()
    except Exception:
        return JsonResponse({'detail': 'Datos inválidos'}, status=400)
    if not firma_imagen:
        return JsonResponse({'detail': 'Firma requerida'}, status=400)
    coord.firma_imagen = firma_imagen
    coord.save(update_fields=['firma_imagen'])
    return JsonResponse({'ok': True})


@login_required
def apc_logout(request: HttpRequest):
    django_logout(request)
    return redirect('login')
