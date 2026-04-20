"""
Exportación de listados a Excel (.xlsx). Misma lógica de filtro por rol y búsqueda que las vistas ListView.
"""
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.http import HttpResponse
from openpyxl import Workbook

from .access_control import filter_queryset_by_role
from .models import (
    AccionTutela,
    DerechoPeticion,
    PagoSentenciaJudicial,
    Peritaje,
    ProcesoAdministrativoSancionatorio,
    ProcesoExtrajudicial,
    ProcesoJudicialActiva,
    ProcesoJudicialPasiva,
    ProcesoJudicialTerminado,
    RequerimientoEnteControl,
)
from .query_helpers import filter_charfield_dmy_range, filter_tutela_by_month_year, is_dmy_string

Usuario = get_user_model()

SKIP_FIELD_NAMES = frozenset({'password'})


def _apply_search(qs, term, fields):
    if not term or not fields:
        return qs
    cond = Q()
    for field in fields:
        cond |= Q(**{f'{field}__icontains': term})
    return qs.filter(cond)


def _tutela_filters(qs, get_params):
    mes = get_params.get('mes', '').strip()
    anio = get_params.get('anio', '').strip()
    if mes.isdigit() and anio.isdigit():
        qs = filter_tutela_by_month_year(qs, int(mes), int(anio))
    fd = get_params.get('fecha_desde', '').strip()
    fh = get_params.get('fecha_hasta', '').strip()
    if fd and fh and is_dmy_string(fd) and is_dmy_string(fh):
        qs = filter_charfield_dmy_range(qs, 'fecha_llegada', fd, fh)
    else:
        if fd:
            qs = qs.filter(fecha_llegada__icontains=fd)
        if fh:
            qs = qs.filter(fecha_llegada__icontains=fh)
    return qs


def _extrajudicial_branch(qs, slug):
    if slug == 'extrajudiciales_conciliados':
        return qs.filter(
            Q(clasificacion__icontains='conciliado') & ~Q(clasificacion__icontains='no concili')
        )
    if slug == 'extrajudiciales_no_conciliados':
        return qs.filter(
            Q(clasificacion__icontains='no concili')
            | Q(clasificacion__isnull=True)
            | Q(clasificacion='')
        )
    return qs


EXPORT_SLUGS = frozenset({
    'usuarios',
    'tutelas',
    'peticiones',
    'procesos_activos',
    'procesos_pasivos',
    'procesos_terminados',
    'peritajes',
    'pagos',
    'sancionatorios',
    'requerimientos',
    'extrajudiciales',
    'extrajudiciales_conciliados',
    'extrajudiciales_no_conciliados',
})

_EXPORT_META = {
    'usuarios': {
        'model': Usuario,
        'search_fields': ('username', 'first_name', 'last_name', 'email', 'nick', 'rol'),
        'extra': None,
    },
    'tutelas': {
        'model': AccionTutela,
        'search_fields': (
            'num_reparto', 'fecha_correo', 'solicitante', 'peticionario', 'causa',
            'accionante', 'identificacion_accionante', 'num_proceso', 'despacho_judicial',
            'abogado_responsable', 'tipo_tramite', 'observaciones',
        ),
        'extra': 'tutela',
    },
    'peticiones': {
        'model': DerechoPeticion,
        'search_fields': (
            'num_reparto', 'fecha_correo', 'nombre_persona_solicitante', 'peticionario',
            'causa_peticion', 'abogado_responsable', 'cedula_persona_solicitante',
            'num_rad_interno',
        ),
        'extra': None,
    },
    'procesos_activos': {
        'model': ProcesoJudicialActiva,
        'search_fields': (
            'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
        ),
        'extra': None,
    },
    'procesos_pasivos': {
        'model': ProcesoJudicialPasiva,
        'search_fields': (
            'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
            'medio_control',
        ),
        'extra': None,
    },
    'procesos_terminados': {
        'model': ProcesoJudicialTerminado,
        'search_fields': (
            'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
            'medio_control',
        ),
        'extra': None,
    },
    'peritajes': {
        'model': Peritaje,
        'search_fields': (
            'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
            'demandante', 'demandado', 'abogado_responsable', 'perito_asignado', 'asunto', 'num_reparto',
        ),
        'extra': None,
    },
    'pagos': {
        'model': PagoSentenciaJudicial,
        'search_fields': (
            'num_proceso', 'fecha_pago', 'despacho_tramitante', 'medio_control',
            'demandante', 'demandado', 'abogado_responsable', 'valor_pagado', 'estado', 'tipo_pago',
        ),
        'extra': None,
    },
    'sancionatorios': {
        'model': ProcesoAdministrativoSancionatorio,
        'search_fields': (
            'num_proceso', 'fecha_requerimiento', 'entidad', 'causa', 'estado',
            'entidad_solicitante_requerimiento', 'objeto_requerimiento',
        ),
        'extra': None,
    },
    'requerimientos': {
        'model': RequerimientoEnteControl,
        'search_fields': (
            'num_reparto', 'num_proceso', 'fecha_correo_electronico',
            'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable', 'tipo_tramite',
        ),
        'extra': None,
    },
    'extrajudiciales': {
        'model': ProcesoExtrajudicial,
        'search_fields': (
            'demandante', 'demandado', 'apoderado', 'medio_control', 'despacho_conocimiento', 'estado', 'clasificacion',
        ),
        'extra': 'extrajudicial',
    },
    'extrajudiciales_conciliados': {
        'model': ProcesoExtrajudicial,
        'search_fields': (
            'demandante', 'demandado', 'apoderado', 'medio_control', 'despacho_conocimiento', 'estado', 'clasificacion',
        ),
        'extra': 'extrajudicial',
    },
    'extrajudiciales_no_conciliados': {
        'model': ProcesoExtrajudicial,
        'search_fields': (
            'demandante', 'demandado', 'apoderado', 'medio_control', 'despacho_conocimiento', 'estado', 'clasificacion',
        ),
        'extra': 'extrajudicial',
    },
}


def get_export_queryset(slug, user, get_params):
    if slug not in EXPORT_SLUGS:
        return None, None
    meta = _EXPORT_META[slug]
    model = meta['model']
    qs = model.objects.all().order_by('-pk')
    if slug != 'usuarios':
        qs = filter_queryset_by_role(qs, user, model)
    term = (get_params.get('q') or '').strip()
    qs = _apply_search(qs, term, meta['search_fields'])
    if meta['extra'] == 'tutela':
        qs = _tutela_filters(qs, get_params)
    elif meta['extra'] == 'extrajudicial':
        qs = _extrajudicial_branch(qs, slug)
    return model, qs


def _cell_value(field, obj):
    raw = field.value_from_object(obj)
    if raw is None:
        return ''
    if isinstance(field, FileField):
        try:
            return raw.name if raw else ''
        except Exception:
            return str(raw)
    if hasattr(raw, 'isoformat'):
        return raw.isoformat()
    return str(raw)


def _export_fields_for_model(model):
    fields = []
    for f in model._meta.concrete_fields:
        if f.name in SKIP_FIELD_NAMES:
            continue
        if isinstance(f, (ForeignKey, OneToOneField)):
            continue
        fields.append(f)
    return fields


def build_excel_response(slug, queryset, model):
    fields = _export_fields_for_model(model)
    headers = [str(f.verbose_name or f.name) for f in fields]

    wb = Workbook()
    ws = wb.active
    ws.title = slug[:31] if slug else 'export'
    ws.append(headers)
    for obj in queryset.iterator(chunk_size=500):
        row = [_cell_value(f, obj) for f in fields]
        ws.append(row)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f'export_{slug}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    resp = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
    return resp
