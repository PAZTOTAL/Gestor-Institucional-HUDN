"""
Filtrado por rol (paridad con getAllByUser del backend Node).
"""
from django.db.models import Q


def filter_queryset_by_role(queryset, user, model, active_usernames=None):
    """
    Restringe el queryset para abogados; admin/super ven todo. 
    Si user es None, se asume contexto global (ej. reportes).
    
    active_usernames: Lista opcional de nombres de usuario permitidos (para optimizar).
    """
    fields = {f.name for f in model._meta.get_fields()}
    
    # 1. Definir lista de usuarios activos si no se provee
    if active_usernames is None and 'usuario_carga' in fields:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Buscamos tanto 'defenjur' como 'legal' para evitar inconsistencias
        active_usernames = User.objects.filter(
            Q(permisos_app__app_label__in=['defenjur', 'legal'], permisos_app__permitido=True) |
            ~Q(perfil__legal_rol='INVITADO') |
            Q(is_superuser=True)
        ).values_list('username', flat=True)

    # 2. Caso Contexto Global (user=None)
    if user is None:
        if 'usuario_carga' in fields and active_usernames is not None:
            return queryset.filter(usuario_carga__in=active_usernames)
        return queryset
        
    # 3. Caso Usuario No Autenticado
    if not user.is_authenticated:
        return queryset.none()

    # 4. Caso Admin/Superusuario
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
    is_admin = user.is_superuser or rol == 'administrador'
    
    # Aplicar filtro de seguridad (solo registros de usuarios activos)
    if 'usuario_carga' in fields and not user.is_superuser:
        queryset = queryset.filter(usuario_carga__in=active_usernames)

    if is_admin:
        return queryset

    # 5. Caso Abogado (Filtro de Propiedad)
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
