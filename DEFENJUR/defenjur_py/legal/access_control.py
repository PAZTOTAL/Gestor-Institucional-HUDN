"""
Filtrado por rol (paridad con getAllByUser del backend Node).
"""
from django.db.models import Q


def filter_queryset_by_role(queryset, user, model):
    """Restringe el queryset para abogados; admin/super ven todo."""
    if user.is_superuser or getattr(user, 'rol', '').lower() == 'administrador':
        return queryset

    if getattr(user, 'rol', '').lower() == 'abogado':
        name = user.get_full_name() or user.username
        nick = getattr(user, 'nick', '') or name
        filter_args = Q()
        fields = {f.name for f in model._meta.get_fields()}
        if 'abogado_responsable' in fields:
            filter_args |= Q(abogado_responsable__icontains=name) | Q(abogado_responsable__icontains=nick)
        if 'apoderado' in fields:
            filter_args |= Q(apoderado__icontains=name) | Q(apoderado__icontains=nick)
        if filter_args:
            return queryset.filter(filter_args)

    return queryset
