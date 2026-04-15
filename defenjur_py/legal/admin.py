from django.contrib import admin
from .models import (
    ProcesoExtrajudicial, ProcesoJudicialActiva, 
    ProcesoJudicialPasiva, DerechoPeticion, AccionTutela, 
    ArchivoAdjunto, Peritaje, PagoSentenciaJudicial, 
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio,
    RequerimientoEnteControl
)

@admin.register(AccionTutela)
class AccionTutelaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_reparto', 'fecha_correo', 'solicitante', 'peticionario',
        'accionante', 'abogado_responsable', 'fecha_llegada',
    ]
    search_fields = [
        'accionante', 'solicitante', 'peticionario', 'causa',
        'identificacion_accionante', 'num_proceso', 'num_reparto',
    ]
    list_filter = ['abogado_responsable', 'area_responsable']

@admin.register(PagoSentenciaJudicial)
class PagoSentenciaJudicialAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_pago', 'despacho_tramitante',
        'medio_control', 'demandante', 'demandado', 'valor_pagado', 'estado',
    ]
    search_fields = [
        'num_proceso', 'fecha_pago', 'despacho_tramitante', 'medio_control',
        'demandante', 'demandado', 'abogado_responsable',
    ]
    list_filter = ['estado']


@admin.register(Peritaje)
class PeritajeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
        'demandante', 'demandado', 'abogado_responsable', 'perito_asignado',
    ]
    search_fields = [
        'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
        'demandante', 'demandado', 'abogado_responsable', 'asunto',
    ]


@admin.register(DerechoPeticion)
class DerechoPeticionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_reparto', 'fecha_correo', 'nombre_persona_solicitante',
        'peticionario', 'abogado_responsable',
    ]
    search_fields = [
        'num_reparto', 'fecha_correo', 'nombre_persona_solicitante', 'peticionario',
        'causa_peticion', 'abogado_responsable', 'cedula_persona_solicitante',
    ]

@admin.register(ProcesoAdministrativoSancionatorio)
class ProcesoAdministrativoSancionatorioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_requerimiento', 'entidad',
        'estado', 'entidad_solicitante_requerimiento',
    ]
    search_fields = [
        'num_proceso', 'fecha_requerimiento', 'entidad', 'causa', 'estado',
        'entidad_solicitante_requerimiento', 'objeto_requerimiento',
    ]
    list_filter = ['estado']


@admin.register(ProcesoJudicialActiva)
class ProcesoJudicialActivaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    ]
    search_fields = [
        'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    ]


@admin.register(ProcesoJudicialPasiva)
class ProcesoJudicialPasivaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    ]
    search_fields = [
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
        'medio_control',
    ]


@admin.register(ProcesoJudicialTerminado)
class ProcesoJudicialTerminadoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    ]
    search_fields = [
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
        'medio_control',
    ]


@admin.register(RequerimientoEnteControl)
class RequerimientoEnteControlAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_reparto', 'num_proceso', 'fecha_correo_electronico',
        'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable',
    ]
    search_fields = [
        'num_reparto', 'num_proceso', 'fecha_correo_electronico',
        'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable', 'tipo_tramite',
    ]


admin.site.register(ProcesoExtrajudicial)
admin.site.register(ArchivoAdjunto)
