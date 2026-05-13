from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def _perfil(user):
    return getattr(user, '_perfil_cache', None) or getattr(user, 'perfil', None)


def es_admin_global(user):
    if user.is_superuser:
        return True
    p = _perfil(user)
    return bool(p and p.categoria == 'ADMIN')


def get_admin_tercerizada(user):
    """Retorna AdministradorTercerizada activo del usuario, o None."""
    try:
        at = user.admin_tercerizada
        return at if at.activo else None
    except Exception:
        return None


def get_empresa_del_admin(user):
    at = get_admin_tercerizada(user)
    return at.empresa if at else None


def puede_gestionar_tercerizada(user):
    return es_admin_global(user) or get_admin_tercerizada(user) is not None


def solo_admin_global(view_func):
    """Decorador: solo el administrador global puede acceder."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not es_admin_global(request.user):
            messages.error(request, 'Solo el Administrador general puede realizar esta acción.')
            return redirect('tercerizadas:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def acceso_tercerizada(view_func):
    """Decorador: admin global o admin de tercerizada activo."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not puede_gestionar_tercerizada(request.user):
            messages.error(request, 'No tiene permisos para acceder a esta sección.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper
