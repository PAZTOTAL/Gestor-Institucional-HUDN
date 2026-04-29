from django.core.cache import cache
from .models import PerfilUsuario, PermisoApp

# TTL del caché de permisos por usuario (5 minutos)
_PERMS_TTL = 300

class UserPermissionsMiddleware:
    """
    Precarga perfil y permisos del usuario usando Django cache.
    Así no se hacen queries a BD en cada request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            uid = request.user.pk

            # 1. Perfil — caché por user id
            perfil_key = f'user_perfil_{uid}'
            perfil = cache.get(perfil_key)
            if perfil is None:
                try:
                    perfil = request.user.perfil
                except (PerfilUsuario.DoesNotExist, AttributeError):
                    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
                cache.set(perfil_key, perfil, _PERMS_TTL)
            request.user._perfil_cache = perfil

            # 2. Permisos de apps — Consulta directa para sincronización instantánea
            perms = set(
                PermisoApp.objects.filter(user=request.user, permitido=True)
                .values_list('app_label', flat=True)
            )
            request.user._permisos_apps_cache = perms

        return self.get_response(request)
