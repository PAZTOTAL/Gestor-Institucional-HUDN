from django import template
from ..access_control import filter_queryset_by_role

register = template.Library()

@register.filter
def can_manage(obj, user):
    """
    Uso: {% if tutela|can_manage:request.user %}
    Verifica si el usuario es administrador o dueño del registro.
    """
    if not user or not user.is_authenticated:
        return False
    
    # Si el objeto es None (por ejemplo en botones de creación global), check de rol
    if obj is None:
        return True # Por defecto dejamos crear a logueados, el backend filtrará
    
    # Usamos la lógica de filter_queryset_by_role pero para un solo objeto
    model = type(obj)
    qs = model.objects.filter(pk=obj.pk)
    filtered_qs = filter_queryset_by_role(qs, user, model)
    return filtered_qs.exists()

@register.filter
def has_module_perm(user, model_name):
    """
    Uso: {% if user|has_module_perm:'acciontutela' %}
    Verifica si el usuario tiene permiso explícito para el módulo.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    
    # El administrador global tiene permiso a todo
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
    if rol == 'administrador':
        return True
    
    from usuarios.models import PermisoModelo
    return PermisoModelo.objects.filter(
        user=user, app_label='defenjur', model_name=model_name, permitido=True
    ).exists()
