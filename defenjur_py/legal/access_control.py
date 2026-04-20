"""
Filtrado por rol (paridad con getAllByUser del backend Node).
"""
from django.db.models import Q


def filter_queryset_by_role(queryset, user, model):
    """Restringe el queryset para abogados; admin/super ven todo."""
    if not user.is_authenticated:
        return queryset.none()
        
    if user.is_superuser:
        return queryset

    # Obtener rol y nick desde el perfil (Gestor Institucional) o desde el objeto user (Stand-alone)
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
    nick = getattr(user, 'nick', None) or getattr(perfil, 'legal_nick', '') or ''
    
    if rol == 'administrador':
        return queryset

    if rol == 'abogado':
        name = user.get_full_name() or user.username
        effective_nick = nick or name
        filter_args = Q()
        fields = {f.name for f in model._meta.get_fields()}
        if 'abogado_responsable' in fields:
            filter_args |= Q(abogado_responsable__icontains=name) | Q(abogado_responsable__icontains=effective_nick)
        if 'apoderado' in fields:
            filter_args |= Q(apoderado__icontains=name) | Q(apoderado__icontains=effective_nick)
        if filter_args:
            return queryset.filter(filter_args)

    return queryset
