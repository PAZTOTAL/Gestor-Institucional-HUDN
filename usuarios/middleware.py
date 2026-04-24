from .models import PerfilUsuario, PermisoApp

class UserPermissionsMiddleware:
    """
    Middleware para consolidar la carga de perfil y permisos del usuario
    en una sola consulta al inicio del request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 0. Saltar para rutas públicas/críticas
        path = request.path_info
        if any(path.startswith(p) for p in ['/login', '/logout', '/accounts/login', '/accounts/logout', '/admin/login']):
            return self.get_response(request)

        if request.user.is_authenticated:
            cache_key = f'user_data_cache_{request.user.id}'
            from django.core.cache import cache
            user_data = cache.get(cache_key)

            if user_data:
                request.user._perfil_cache = user_data['perfil']
                request.user._permisos_apps_cache = user_data['permisos']
            else:
                # 1. Precargar Perfil
                try:
                    perfil = request.user.perfil
                except (PerfilUsuario.DoesNotExist, AttributeError):
                    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
                
                request.user._perfil_cache = perfil

                # 2. Precargar Permisos de Aplicaciones
                perms = set(
                    PermisoApp.objects.filter(user=request.user, permitido=True)
                    .values_list('app_label', flat=True)
                )
                request.user._permisos_apps_cache = perms

                # Guardar en cache por 5 minutos
                cache.set(cache_key, {'perfil': perfil, 'permisos': perms}, 300)

        return self.get_response(request)
