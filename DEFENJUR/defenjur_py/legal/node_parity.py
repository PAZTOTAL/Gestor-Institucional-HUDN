"""
Lógica equivalente a getByDateRange / totales de defenjur-back/controllers (API JSON).
"""
from .models import (
    AccionTutela,
    DerechoPeticion,
    PagoSentenciaJudicial,
    Peritaje,
    RequerimientoEnteControl,
    ProcesoAdministrativoSancionatorio,
)
from .query_helpers import filter_charfield_dmy_range


def _resolve_campo_fecha(spec, tipo_busqueda):
    tipos = spec.get('tipo_validos') or {}
    if tipo_busqueda and tipo_busqueda in tipos:
        return tipos[tipo_busqueda]
    return spec['default']


def _apply_opcionales(qs, request_get, pairs):
    for param_name, orm_lookup, mode in pairs:
        val = request_get.get(param_name, '').strip()
        if not val:
            continue
        if mode == 'exact':
            qs = qs.filter(**{orm_lookup: val})
        else:
            qs = qs.filter(**{f'{orm_lookup}__icontains': val})
    return qs


def estadisticas_rango_por_modulo(request_get):
    """
    Replica respuestas tipo getByDateRange de los controllers Node.
    GET: modulo, fechaInicio, fechaFin, tipoBusqueda (opcional), + filtros por módulo.
    """
    modulo = (request_get.get('modulo') or '').strip()
    fi = (request_get.get('fechaInicio') or '').strip()
    ff = (request_get.get('fechaFin') or '').strip()
    if not fi or not ff:
        return None, {'error': 'Debe proporcionar fechaInicio y fechaFin (dd/mm/yyyy).'}

    configs = {
        'acciones_tutela': {
            'model': AccionTutela,
            'response_total_table': 'total_acciones_tutela',
            'fecha': {
                'default': 'fecha_llegada',
                'tipo_validos': {'fechaCorreo': 'fecha_correo', 'fechaLlegada': 'fecha_llegada'},
            },
            'opcionales': [
                ('objetoTutela', 'objeto_tutela', 'exact'),
                ('asuntoTutela', 'asunto_tutela', 'icontains'),
                ('abogadoResponsable', 'abogado_responsable', 'icontains'),
                ('solicitante', 'solicitante', 'icontains'),
                ('peticionario', 'peticionario', 'icontains'),
                ('causa', 'causa', 'icontains'),
            ],
        },
        'derechos_peticion': {
            'model': DerechoPeticion,
            'response_total_table': 'total_derechos_peticion',
            'fecha': {
                'default': 'fecha_correo',
                'tipo_validos': {
                    'fecha_correo': 'fecha_correo',
                    'fecha_reparto': 'fecha_reparto',
                    'fecha_remitente_peticion': 'fecha_remitente_peticion',
                },
            },
            'opcionales': [
                ('numReparto', 'num_reparto', 'icontains'),
                ('abogadoResponsable', 'abogado_responsable', 'icontains'),
                ('causaPeticion', 'causa_peticion', 'icontains'),
                ('causa', 'causa_peticion', 'icontains'),
                ('peticionario', 'peticionario', 'icontains'),
                ('solicitante', 'nombre_persona_solicitante', 'icontains'),
            ],
        },
        'pagos_sentencias_judiciales': {
            'model': PagoSentenciaJudicial,
            'response_total_table': 'total_pagos_sentencias',
            'fecha': {
                'default': 'fecha_pago',
                'tipo_validos': {
                    'fecha_pago': 'fecha_pago',
                    'fecha_ejecutoria_sentencia': 'fecha_ejecutoria_sentencia',
                },
            },
            'opcionales': [
                ('numProceso', 'num_proceso', 'icontains'),
                ('despachoTramitante', 'despacho_tramitante', 'icontains'),
                ('demandante', 'demandante', 'icontains'),
                ('demandado', 'demandado', 'icontains'),
                ('abogadoResponsable', 'abogado_responsable', 'icontains'),
                ('medioControl', 'medio_control', 'icontains'),
                ('estado', 'estado', 'exact'),
                ('tipoPago', 'tipo_pago', 'icontains'),
            ],
        },
        'peritajes': {
            'model': Peritaje,
            'response_total_table': 'total_peritajes',
            'fecha': {
                'default': 'fecha_correo_electronico',
                'tipo_validos': {
                    'fecha_correo_electronico': 'fecha_correo_electronico',
                    'fecha_reparto': 'fecha_reparto',
                    'fecha_asignar_perito': 'fecha_asignar_perito',
                },
            },
            'opcionales': [
                ('numProceso', 'num_proceso', 'icontains'),
                ('entidadRequirente', 'entidad_remitente_requerimiento', 'icontains'),
                ('demandante', 'demandante', 'icontains'),
                ('demandado', 'demandado', 'icontains'),
                ('abogadoResponsable', 'abogado_responsable', 'icontains'),
                ('asunto', 'asunto', 'icontains'),
                ('peritoAsignado', 'perito_asignado', 'icontains'),
                ('pagoHonorarios', 'pago_honorarios', 'exact'),
            ],
        },
        'requerimientos_entes_control': {
            'model': RequerimientoEnteControl,
            'response_total_table': 'total_requerimientos_entes_control',
            'fecha': {
                'default': 'fecha_correo_electronico',
                'tipo_validos': {
                    'fecha_correo_electronico': 'fecha_correo_electronico',
                    'fecha_reparto': 'fecha_reparto',
                    'fecha_respuesta_tramite': 'fecha_respuesta_tramite',
                },
            },
            'opcionales': [
                ('numReparto', 'num_reparto', 'icontains'),
                ('numProceso', 'num_proceso', 'icontains'),
                ('abogadoResponsable', 'abogado_responsable', 'icontains'),
                ('asunto', 'asunto', 'icontains'),
                ('entidadRemitente', 'entidad_remitente_requerimiento', 'icontains'),
                ('tipoTramite', 'tipo_tramite', 'icontains'),
            ],
        },
        'procesos_administrativos_sancionatorios': {
            'model': ProcesoAdministrativoSancionatorio,
            'response_total_table': 'total_procesos_adm_sancionatorios',
            'fecha': {
                'default': 'fecha_requerimiento',
                'tipo_validos': {
                    'fecha_requerimiento': 'fecha_requerimiento',
                    'fecha_dar_tramite_desde': 'fecha_dar_tramite_desde',
                    'fecha_dar_tramite_hasta': 'fecha_dar_tramite_hasta',
                },
            },
            'opcionales': [
                ('numProceso', 'num_proceso', 'icontains'),
                ('entidad', 'entidad', 'icontains'),
                ('causa', 'causa', 'icontains'),
                ('estado', 'estado', 'exact'),
                ('entidadSolicitante', 'entidad_solicitante_requerimiento', 'icontains'),
                ('objetoRequerimiento', 'objeto_requerimiento', 'icontains'),
            ],
        },
    }

    if modulo not in configs:
        return None, {
            'error': 'módulo no válido',
            'validos': list(configs.keys()),
        }

    cfg = configs[modulo]
    Model = cfg['model']
    campo = _resolve_campo_fecha(cfg['fecha'], request_get.get('tipoBusqueda', '').strip())

    qs = Model.objects.all()
    qs = filter_charfield_dmy_range(qs, campo, fi, ff)
    qs = _apply_opcionales(qs, request_get, cfg['opcionales'])

    total_tabla = Model.objects.count()
    total_filtrado = qs.count()

    body = {
        cfg['response_total_table']: total_tabla,
        'total_filtrado': total_filtrado,
        'total': total_filtrado,
        'campo_fecha_usado': campo,
        'filtros_aplicados': {
            'fechaInicio': fi,
            'fechaFin': ff,
            'tipoBusqueda': campo,
            'modulo': modulo,
        },
    }
    return body, None
