from usuarios.models import PerfilUsuario, PermisoApp


def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
    
    # Usar datos precargados por UserPermissionsMiddleware
    perfil = getattr(request.user, '_perfil_cache', None)
    allowed_apps_list = getattr(request.user, '_permisos_apps_cache', [])
    
    if not perfil:
        from .models import PerfilUsuario
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    
    cat = perfil.categoria
    return {
        'user_categoria': cat,
        'perfil': perfil,
        'is_admin': cat == 'ADMIN' or request.user.is_superuser,
        'can_edit': cat in ('ADMIN', 'EDITOR') or request.user.is_superuser,
        'can_delete': cat == 'ADMIN' or request.user.is_superuser,
        'can_print': cat in ('ADMIN', 'EDITOR', 'IMPRESOR') or request.user.is_superuser,
        'permisos_apps_global': list(allowed_apps_list) if not request.user.is_superuser else 'ALL',
    }
