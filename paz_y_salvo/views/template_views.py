import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.http import HttpRequest

from ..models import ListaBlanca
from ..auth import create_token, decode_token


def _get_lista_blanca(username: str):
    try:
        return ListaBlanca.objects.get(usunombre=username, activo=True)
    except ListaBlanca.DoesNotExist:
        return None


def _make_avatar(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return full_name[:2].upper() if full_name else 'U'


def _get_aplicativo_nombre(user) -> str:
    """
    Retorna el nombre del aplicativo Django (first_name + last_name).
    Elimina palabras duplicadas caso-insensibles causadas por sincronizaciones
    previas que combinaron el nombre del aplicativo con el de lista blanca.
    NUNCA usa lb.nombre — solo usa los campos Django del usuario.
    """
    fn = (user.first_name or '').strip()
    ln = (user.last_name or '').strip()
    full = f"{fn} {ln}".strip()
    if not full:
        return user.username
    seen: set = set()
    unique_words = []
    for word in full.split():
        key = word.lower()
        if key not in seen:
            seen.add(key)
            unique_words.append(word)
    return ' '.join(unique_words)


@login_required
def paz_y_salvo_landing(request: HttpRequest):
    lb = _get_lista_blanca(request.user.username)
    username = _get_aplicativo_nombre(request.user)
    avatar = _make_avatar(username)

    rol_info = None
    if lb is not None:
        rol_info = {
            'rol': lb.rol,
            'area_nombre': lb.area.nombre if lb.area else None,
        }

    return render(request, 'paz_y_salvo/landing.html', {
        'username': username,
        'avatar': avatar,
        'rol_info': rol_info,
    })


@login_required
def paz_y_salvo_panel(request: HttpRequest):
    lb = _get_lista_blanca(request.user.username)
    if lb is None:
        return redirect('paz_y_salvo:pys_landing')

    # Nombre del aplicativo Django únicamente — NO se usa lb.nombre para display
    django_nombre = _get_aplicativo_nombre(request.user)
    django_avatar = _make_avatar(django_nombre)

    payload = {
        'sub': request.user.username,
        'usunombre': lb.usunombre,
        'nombre': django_nombre,
        'rol': lb.rol,
        'area_id': lb.area_id,
    }
    token = create_token(payload)

    pys_user = {
        'usunombre': lb.usunombre,
        'nombre': django_nombre,
        'rol': lb.rol,
        'area_id': lb.area_id,
        'avatar': django_avatar,
        'area_nombre': lb.area.nombre if lb.area else None,
    }

    return render(request, 'paz_y_salvo/index.html', {
        'pys_token': token,
        'pys_user_json': json.dumps(pys_user, ensure_ascii=False),
        'pys_user': pys_user,
        'django_nombre': django_nombre,
    })


def solicitud_publica_page(request: HttpRequest):
    return render(request, 'paz_y_salvo/solicitud_publica.html')


def validar_por_token_page(request: HttpRequest):
    token = request.GET.get('token', '')
    error = None

    if token:
        try:
            decode_token(token)
        except ValueError as e:
            error = str(e)

    return render(request, 'paz_y_salvo/validar.html', {
        'token': token,
        'error': error,
    })


@login_required
def pys_logout_view(request: HttpRequest):
    django_logout(request)
    return redirect('login')
