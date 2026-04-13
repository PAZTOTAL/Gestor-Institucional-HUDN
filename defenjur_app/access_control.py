"""
Filtrado por rol para DEFENJUR (integrado con PerfilUsuario del sistema principal).
"""
from django.db.models import Q

def filter_queryset_by_role(queryset, user, model):
    """Restringe el queryset para abogados; admin/super ven todo."""
    if not user.is_authenticated:
        return queryset.none()
        
    if user.is_superuser:
        return queryset
        
    # Obtener el rol desde el perfil integrado
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(perfil, 'legal_rol', '') or '').lower()
    
    if rol == 'administrador':
        return queryset

    if rol == 'abogado':
        name = user.get_full_name() or user.username
        nick = getattr(perfil, 'legal_nick', '') or name
        filter_args = Q()
        fields = {f.name for f in model._meta.get_fields()}
        if 'abogado_responsable' in fields:
            filter_args |= Q(abogado_responsable__icontains=name) | Q(abogado_responsable__icontains=nick)
        if 'apoderado' in fields:
            filter_args |= Q(apoderado__icontains=name) | Q(apoderado__icontains=nick)
        if filter_args:
            return queryset.filter(filter_args)

    return queryset
