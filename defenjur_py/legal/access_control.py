"""
Filtrado por rol (paridad con getAllByUser del backend Node).
"""
from django.db.models import Q


def filter_queryset_by_role(queryset, user, model):
    """Restringe el queryset para abogados; admin/super ven todo. 
    Si user es None, se asume contexto global (ej. reportes)."""
    if user is None:
        # En contexto global, aún filtramos por usuarios activos si el modelo tiene usuario_carga
        fields = {f.name for f in model._meta.get_fields()}
        if 'usuario_carga' in fields:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            active_usernames = User.objects.filter(
                Q(permisos_app__app_label='defenjur', permisos_app__permitido=True) |
                ~Q(perfil__legal_rol='INVITADO') |
                Q(is_superuser=True)
            ).values_list('username', flat=True)
            return queryset.filter(usuario_carga__in=active_usernames)
        return queryset
        
    if not user.is_authenticated:
        return queryset.none()

    # Si no es superuser ni admin, aplicamos filtro de propiedad
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
    is_admin = user.is_superuser or rol == 'administrador'
    
    # Filtro de seguridad: Solo registros de usuarios con Permiso Principal activo
    fields = {f.name for f in model._meta.get_fields()}
    if 'usuario_carga' in fields and not user.is_superuser:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        active_usernames = User.objects.filter(
            Q(permisos_app__app_label='legal', permisos_app__permitido=True) |
            ~Q(perfil__legal_rol='INVITADO') |
            Q(is_superuser=True)
        ).values_list('username', flat=True)
        queryset = queryset.filter(usuario_carga__in=active_usernames)

    if is_admin:
        return queryset

    nick = getattr(user, 'nick', None) or getattr(perfil, 'legal_nick', '') or ''
    if rol == 'abogado':
        name = user.get_full_name() or user.username
        effective_nick = nick or name
        filter_args = Q()
        if 'abogado_responsable' in fields:
            filter_args |= Q(abogado_responsable__icontains=name) | Q(abogado_responsable__icontains=effective_nick)
        if 'apoderado' in fields:
            filter_args |= Q(apoderado__icontains=name) | Q(apoderado__icontains=effective_nick)
        if filter_args:
            return queryset.filter(filter_args)

    return queryset
