"""
API JSON tipo getAll / getDetail (paridad con controllers Node).
Requiere sesión iniciada (mismo criterio que el resto de la app).
"""
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .access_control import filter_queryset_by_role
from .models import (
    AccionTutela,
    DerechoPeticion,
    ProcesoExtrajudicial,
    ProcesoJudicialActiva,
    ProcesoJudicialPasiva,
    ProcesoJudicialTerminado,
    Peritaje,
    PagoSentenciaJudicial,
    ProcesoAdministrativoSancionatorio,
    RequerimientoEnteControl,
)

# slug en URL → modelo (orden estable para documentación)
ENTITY_BY_SLUG = {
    'acciones-tutela': AccionTutela,
    'derechos-peticion': DerechoPeticion,
    'procesos-extrajudiciales': ProcesoExtrajudicial,
    'procesos-judiciales-activa': ProcesoJudicialActiva,
    'procesos-judiciales-pasiva': ProcesoJudicialPasiva,
    'procesos-judiciales-terminados': ProcesoJudicialTerminado,
    'peritajes': Peritaje,
    'pagos-sentencias-judiciales': PagoSentenciaJudicial,
    'procesos-administrativos-sancionatorios': ProcesoAdministrativoSancionatorio,
    'requerimientos-entes-control': RequerimientoEnteControl,
}


def serialize_instance(obj):
    """Campos escalares del modelo (sin relaciones M2M)."""
    out = {'id': obj.pk}
    for f in obj._meta.concrete_fields:
        if f.primary_key:
            continue
        if isinstance(f, (models.FileField, models.ImageField)):
            val = f.value_from_object(obj)
            try:
                out[f.name] = val.url if val else None
            except Exception:
                out[f.name] = str(val) if val else None
            continue
        if isinstance(f, models.ForeignKey):
            continue
        val = f.value_from_object(obj)
        if hasattr(val, 'isoformat'):
            val = val.isoformat()
        out[f.name] = val
    return out


def api_entity_list(request, slug):
    model = ENTITY_BY_SLUG.get(slug)
    if not model:
        return JsonResponse({'error': 'Entidad no válida', 'valid_slugs': list(ENTITY_BY_SLUG)}, status=404)
    qs = model.objects.all().order_by('-pk')
    qs = filter_queryset_by_role(qs, request.user, model)
    try:
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(max(1, int(request.GET.get('page_size', 50))), 500)
    except ValueError:
        return JsonResponse({'error': 'page y page_size deben ser enteros'}, status=400)
    total = qs.count()
    start = (page - 1) * page_size
    rows = qs[start : start + page_size]
    return JsonResponse(
        {
            'entity': slug,
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': [serialize_instance(o) for o in rows],
        }
    )


def api_entity_detail(request, slug, pk):
    model = ENTITY_BY_SLUG.get(slug)
    if not model:
        return JsonResponse({'error': 'Entidad no válida'}, status=404)
    qs = model.objects.all()
    qs = filter_queryset_by_role(qs, request.user, model)
    obj = get_object_or_404(qs, pk=pk)
    return JsonResponse({'entity': slug, 'result': serialize_instance(obj)})


def _wrap(view_fn):
    from django.contrib.auth.decorators import login_required

    return login_required(require_GET(view_fn))

api_entity_list_view = _wrap(api_entity_list)
api_entity_detail_view = _wrap(api_entity_detail)
