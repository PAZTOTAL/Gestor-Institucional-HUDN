from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from usuarios.models import PermisoApp

def valida_acceso(app_label):
    """
    Decorador para verificar si el usuario tiene permiso de acceso a una App específica.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # 1. Superuser bypass
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 2. Check PermisoApp
            try:
                permiso = PermisoApp.objects.get(user=request.user, app_label=app_label)
                if permiso.permitido:
                    return view_func(request, *args, **kwargs)
            except PermisoApp.DoesNotExist:
                pass # No permission record found -> Deny
            
            # 3. Deny if no permission found or permitido=False
            raise PermissionDenied(f"No tienes permiso para acceder al módulo {app_label}.")
            
        return _wrapped_view
    return decorator
