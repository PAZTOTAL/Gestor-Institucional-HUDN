from django.contrib import admin
from .models import (
    MezclaOrden, MezclaPreparacion, MezclaControlCalidad, MezclaDistribucion,
    ReempaqueMedicamento, ReempaqueOrden, ReempaqueControl, ReempaqueMuestreo,
    ConvencionFormaFarmaceutica, Alerta, MedicamentoEsteril,
    UnidosisPeriodo, UnidosisOrden, Funcionario, MedicamentoOncologico,
    OncologicoMatriz, OncologicoMatrizItem, OncologicoOrdenProduccion, OncologicoOrdenItem,
    OncologicoAlistamiento, OncologicoAlistamientoItem,
    NeonatosMatriz, NeonatosMatrizItem, NeonatosMedicamento, NeonatosOrdenProduccion,
    NeonatosOrdenItem, NeonatosAlistamiento, NeonatosAlistamientoItem,
    UnidosisProduccionOrden, NptMatriz, NptMatrizItem, NptOrdenProduccion, NptOrdenItem, NptAlistamiento, NptAlistamientoItem
)

class MezclaPreparacionInline(admin.StackedInline):
    model = MezclaPreparacion
    extra = 0

class MezclaControlCalidadInline(admin.StackedInline):
    model = MezclaControlCalidad
    extra = 0

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'nombre_completo', 'cargo', 'activo')
    search_fields = ('cedula', 'nombre_completo')
    list_filter = ('activo', 'cargo')

@admin.register(UnidosisPeriodo)
class UnidosisPeriodoAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'jefe_produccion')
    search_fields = ('orden_produccion',)

@admin.register(UnidosisOrden)
class UnidosisOrdenAdmin(admin.ModelAdmin):
    list_display = ('lote_interno', 'paciente_nombre', 'medicamento_base', 'periodo')
    list_filter = ('periodo',)
    search_fields = ('lote_interno', 'paciente_nombre')

@admin.register(MedicamentoEsteril)
class MedicamentoEsterilAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'medicamento_1', 'concentracion_1', 'via', 'elaborado_por', 'verificado_por')
    search_fields = ('codigo', 'medicamento_1', 'vehiculo_final', 'elaborado_por')
    list_filter = ('via', 'almacenamiento', 'verificado_por')

@admin.register(MezclaOrden)
class MezclaOrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente_oid', 'tipo_mezcla', 'estado', 'validado_por', 'fecha_solicitud')
    list_filter = ('tipo_mezcla', 'prioridad', 'estado')
    search_fields = ('descripcion_medicamento', 'paciente_oid')
    
    fieldsets = (
        ('Información General', {
            'fields': ('paciente_oid', 'medico_oid', 'tipo_mezcla', 'descripcion_medicamento', 'prioridad', 'estado')
        }),
        ('Validación Orden Médica (FRFAR-156)', {
            'fields': (
                'validado_por', 'fecha_validacion',
                'criterio_prestador', 'criterio_lugar_fecha', 'criterio_paciente', 
                'criterio_tipo_usuario', 'criterio_dci', 'criterio_concentracion',
                'criterio_via_frecuencia', 'criterio_cantidad', 'criterio_indicaciones',
                'criterio_legibilidad', 'criterio_periodo', 'criterio_vigencia'
            )
        }),
        ('Extras', {
            'fields': ('observaciones_clinicas',),
            'classes': ('collapse',)
        }),
    )
    inlines = [MezclaPreparacionInline]

@admin.register(MezclaPreparacion)
class MezclaPreparacionAdmin(admin.ModelAdmin):
    list_display = ('lote_interno', 'orden', 'qf_preparador', 'fecha_inicio', 'fecha_fin')
    search_fields = ('lote_interno', 'tecnico_preparador')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('orden', 'lote_interno', 'cabina_id')
        }),
        ('Trazabilidad de Producción', {
            'fields': ('jefe_produccion', 'qf_preparador', 'alistamiento_por', 'director_tecnico', 'tecnico_preparador')
        }),
        ('Detalle Técnico (FRFAR-177)', {
            'fields': ('viales_ampollas', 'solucion_diluyente', 'volumen_dilucion', 'volumen_dosis', 'vehiculo_volumen_final')
        }),
        ('Proceso', {
            'fields': ('insumos_utilizados', 'fecha_inicio', 'fecha_fin')
        }),
    )
    inlines = [MezclaControlCalidadInline]

@admin.register(MezclaControlCalidad)
class MezclaControlCalidadAdmin(admin.ModelAdmin):
    list_display = ('preparacion', 'aprobado', 'verificado_por', 'aprobado_por', 'fecha_control')
    list_filter = ('aprobado',)
    
    fieldsets = (
        ('Vinculación', {
            'fields': ('preparacion',)
        }),
        ('Control Inicial (CI)', {
            'fields': ('ci_particulas_extranas', 'ci_concordancia_op', 'ci_fugas')
        }),
        ('Control Final (CF)', {
            'fields': ('cf_etiqueta_ok', 'cf_hermeticidad', 'cf_limpieza', 'visual_ok', 'etiquetado_ok', 'hermeticidad_ok')
        }),
        ('Trazabilidad y Liberación', {
            'fields': ('verificado_por', 'aprobado_por', 'aprobado', 'valoracion_final')
        }),
    )

@admin.register(OncologicoMatriz)
class OncologicoMatrizAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'jefe_produccion', 'quien_prepara')
    list_filter = ('fecha',)
    search_fields = ('orden_produccion',)

@admin.register(OncologicoMatrizItem)
class OncologicoMatrizItemAdmin(admin.ModelAdmin):
    list_display = ('lote_interno', 'paciente_nombre', 'medicamento', 'matriz')
    search_fields = ('lote_interno', 'paciente_nombre', 'medicamento')

admin.site.register(MezclaDistribucion)
@admin.register(NeonatosMedicamento)
class NeonatosMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('cod', 'medicamento', 'concentracion', 'forma_farmaceutica', 'administracion', 'almacenamiento')
    search_fields = ('medicamento', 'producto', 'cod_med')
    list_filter = ('forma_farmaceutica', 'administracion')

class NeonatosMatrizItemInline(admin.TabularInline):
    model = NeonatosMatrizItem
    extra = 1

@admin.register(NeonatosMatriz)
class NeonatosMatrizAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'jefe_produccion', 'quien_prepara')
    search_fields = ('orden_produccion',)
    list_filter = ('fecha',)
    inlines = [NeonatosMatrizItemInline]

@admin.register(NeonatosOrdenProduccion)
class NeonatosOrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'fecha')
    search_fields = ('numero_orden',)

@admin.register(NeonatosAlistamiento)
class NeonatosAlistamientoAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'responsable')

@admin.register(UnidosisProduccionOrden)
class UnidosisProduccionAdmin(admin.ModelAdmin):
    list_display = ('lote_interno', 'medicamento', 'fecha', 'elaborado_por')
    search_fields = ('lote_interno', 'medicamento')

class NptMatrizItemInline(admin.TabularInline):
    model = NptMatrizItem
    extra = 1

@admin.register(NptMatriz)
class NptMatrizAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'jefe_produccion', 'qf_preparador')
    search_fields = ('orden_produccion',)
    list_filter = ('fecha',)
    inlines = [NptMatrizItemInline]

@admin.register(NptOrdenProduccion)
class NptOrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'fecha')
    search_fields = ('numero_orden',)

@admin.register(NptAlistamiento)
class NptAlistamientoAdmin(admin.ModelAdmin):
    list_display = ('orden_produccion', 'fecha', 'responsable')

admin.site.register(OncologicoOrdenProduccion)
admin.site.register(OncologicoOrdenItem)
admin.site.register(OncologicoAlistamiento)
admin.site.register(OncologicoAlistamientoItem)

@admin.register(ReempaqueMedicamento)
class ReempaqueMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'concentracion', 'convencion', 'alerta')
    search_fields = ('nombre', 'concentracion')

@admin.register(ReempaqueOrden)
class ReempaqueOrdenAdmin(admin.ModelAdmin):
    list_display = ('lote_interno', 'medicamento', 'lote_fabricante', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'fecha_produccion')
    search_fields = ('lote_interno', 'lote_fabricante', 'medicamento__nombre')

@admin.register(ReempaqueControl)
class ReempaqueControlAdmin(admin.ModelAdmin):
    list_display = ('orden', 'liberado', 'fecha_liberacion')

@admin.register(ConvencionFormaFarmaceutica)
class ConvencionAdmin(admin.ModelAdmin):
    list_display = ('forma_farmaceutica', 'via')
    search_fields = ('forma_farmaceutica', 'via')

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'color')
    search_fields = ('codigo', 'color')

admin.site.register(ReempaqueMuestreo)

@admin.register(MedicamentoOncologico)
class MedicamentoOncologicoAdmin(admin.ModelAdmin):
    list_display = ('cod', 'medicamento', 'concentracion', 'forma_farmaceutica', 'administracion', 'vehiculo', 'almacenamiento')
    search_fields = ('medicamento', 'producto', 'concentracion', 'administracion', 'vehiculo')
    list_filter = ('administracion', 'forma_farmaceutica', 'almacenamiento')
