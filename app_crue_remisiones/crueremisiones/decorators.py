"""
Decoradores de acceso para la aplicación CRUE Remisiones.
"""
from functools import wraps

from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from .models import GRUPO_CRUE_REMISIONES


def crue_required(view_func):
    """
    Decorador que verifica que el usuario esté autenticado y pertenezca
    al grupo 'crue_remisiones'. Si no pertenece, retorna 403.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name=GRUPO_CRUE_REMISIONES).exists():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden(
            'No tiene acceso a la aplicación CRUE Remisiones. '
            'Contacte al administrador del sistema.'
        )
    return wrapper
