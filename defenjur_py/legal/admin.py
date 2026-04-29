from django.contrib import admin
from .models import (
    ProcesoExtrajudicial, ProcesoJudicialActiva, 
    ProcesoJudicialPasiva, DerechoPeticion, AccionTutela, 
    ArchivoAdjunto, Peritaje, PagoSentenciaJudicial, 
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio,
    RequerimientoEnteControl, CatalogoDerechoVulnerado, CatalogoAccionado
)

@admin.register(CatalogoDerechoVulnerado)
class CatalogoDerechoVulneradoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'fecha_registro']
    search_fields = ['nombre']

@admin.register(CatalogoAccionado)
class CatalogoAccionadoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nit', 'nombre', 'fecha_registro']
    search_fields = ['nit', 'nombre']

@admin.register(AccionTutela)
class AccionTutelaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_llegada', 'despacho_judicial', 
        'accionante', 'accionado', 'abogado_responsable'
    ]
    search_fields = ['num_proceso', 'num_reparto', 'abogado_responsable', 'accionante', 'accionado']
    list_filter = ['abogado_responsable']

@admin.register(DerechoPeticion)
class DerechoPeticionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_reparto', 'fecha_correo', 'nombre_persona_solicitante', 
        'peticionario', 'causa_peticion', 'abogado_responsable'
    ]
    search_fields = ['num_reparto', 'abogado_responsable', 'nombre_persona_solicitante', 'peticionario']
    list_filter = ['abogado_responsable']

@admin.register(PagoSentenciaJudicial)
class PagoSentenciaJudicialAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_pago', 'despacho_tramitante', 
        'medio_control', 'demandante', 'demandado'
    ]
    search_fields = ['num_proceso', 'demandante', 'demandado']
    list_filter = ['medio_control', 'estado']

@admin.register(Peritaje)
class PeritajeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_correo_electronico', 
        'entidad_remitente_requerimiento', 'demandante', 'demandado', 'abogado_responsable'
    ]
    search_fields = ['num_proceso', 'abogado_responsable', 'demandante', 'demandado']
    list_filter = ['abogado_responsable']

@admin.register(ProcesoAdministrativoSancionatorio)
class ProcesoAdministrativoSancionatorioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'fecha_requerimiento', 'entidad', 
        'causa', 'estado', 'entidad_solicitante_requerimiento'
    ]
    search_fields = ['num_proceso', 'entidad', 'entidad_solicitante_requerimiento']
    list_filter = ['estado']

@admin.register(ProcesoExtrajudicial)
class ProcesoExtrajudicialAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'demandante', 'demandado', 'apoderado', 
        'medio_control', 'despacho_conocimiento', 'estado'
    ]
    search_fields = ['demandante', 'demandado', 'apoderado']
    list_filter = ['estado', 'medio_control']

@admin.register(ProcesoJudicialActiva)
class ProcesoJudicialActivaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual'
    ]
    search_fields = ['num_proceso', 'apoderado', 'demandante', 'demandado']
    list_filter = ['apoderado', 'medio_control']

@admin.register(ProcesoJudicialPasiva)
class ProcesoJudicialPasivaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual'
    ]
    search_fields = ['num_proceso', 'apoderado', 'demandante', 'demandado']
    list_filter = ['apoderado', 'medio_control']

@admin.register(ProcesoJudicialTerminado)
class ProcesoJudicialTerminadoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual'
    ]
    search_fields = ['num_proceso', 'apoderado', 'demandante', 'demandado']
    list_filter = ['apoderado', 'medio_control']

@admin.register(RequerimientoEnteControl)
class RequerimientoEnteControlAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'num_reparto', 'num_proceso', 'fecha_correo_electronico', 
        'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable'
    ]
    search_fields = ['num_reparto', 'num_proceso', 'abogado_responsable', 'entidad_remitente_requerimiento']
    list_filter = ['abogado_responsable']

admin.site.register(ArchivoAdjunto)
