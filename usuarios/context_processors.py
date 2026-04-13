from usuarios.models import PerfilUsuario, PermisoApp

def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
        
    perfil = getattr(request.user, 'perfil', None)
    if not perfil:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
        
    # Get allowed apps for the user to filter menus
    allowed_apps_list = list(PermisoApp.objects.filter(user=request.user, permitido=True).values_list('app_label', flat=True))
    
    return {
        'user_categoria': perfil.categoria,
        'perfil': perfil, # Full profile for theme and other settings
        'is_admin': perfil.categoria == 'ADMIN' or request.user.is_superuser,
        'can_edit': perfil.categoria in ['ADMIN', 'EDITOR'] or request.user.is_superuser,
        'can_delete': perfil.categoria == 'ADMIN' or request.user.is_superuser,
        'can_print': perfil.categoria in ['ADMIN', 'EDITOR', 'IMPRESOR'] or request.user.is_superuser,
        'permisos_apps_global': allowed_apps_list if not request.user.is_superuser else 'ALL'
    }
