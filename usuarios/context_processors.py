from usuarios.models import PerfilUsuario, PermisoApp


def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
    
    perfil = getattr(request.user, 'perfil', None)
    if not perfil:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    
    # Get allowed apps for the user to filter menus - fresh query on each request
    # for immediate feedback when permissions change
    allowed_apps_list = list(
        PermisoApp.objects.filter(user=request.user, permitido=True)
        .values_list('app_label', flat=True)
    )
    
    cat = perfil.categoria
    return {
        'user_categoria': cat,
        'perfil': perfil,
        'is_admin': cat == 'ADMIN' or request.user.is_superuser,
        'can_edit': cat in ('ADMIN', 'EDITOR') or request.user.is_superuser,
        'can_delete': cat == 'ADMIN' or request.user.is_superuser,
        'can_print': cat in ('ADMIN', 'EDITOR', 'IMPRESOR') or request.user.is_superuser,
        'permisos_apps_global': allowed_apps_list if not request.user.is_superuser else 'ALL',
    }
