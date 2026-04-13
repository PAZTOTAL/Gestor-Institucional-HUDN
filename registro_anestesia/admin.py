from django.contrib import admin
from .models import (
    RegistroAnestesia, EvaluacionPreAnestesica, Monitoreo, Ventilacion,
    Medicamentos, Liquidos, SignosVitales, Tecnica, Salida, Observaciones
)

class EvaluacionInline(admin.StackedInline):
    model = EvaluacionPreAnestesica
    can_delete = False
    verbose_name_plural = 'Evaluación Pre-Anestésica'

class MonitoreoInline(admin.StackedInline):
    model = Monitoreo
    can_delete = False
    verbose_name_plural = 'Monitoreo'

class VentilacionInline(admin.StackedInline):
    model = Ventilacion
    can_delete = False
    verbose_name_plural = 'Ventilación'

class MedicamentosInline(admin.TabularInline):
    model = Medicamentos
    extra = 1
    verbose_name_plural = 'Medicamentos'

class LiquidosInline(admin.StackedInline):
    model = Liquidos
    can_delete = False
    verbose_name_plural = 'Líquidos'

class SignosVitalesInline(admin.TabularInline):
    model = SignosVitales
    extra = 1
    verbose_name_plural = 'Signos Vitales'

class TecnicaInline(admin.StackedInline):
    model = Tecnica
    can_delete = False
    verbose_name_plural = 'Técnica'

class SalidaInline(admin.StackedInline):
    model = Salida
    can_delete = False
    verbose_name_plural = 'Salida'

class ObservacionesInline(admin.StackedInline):
    model = Observaciones
    can_delete = False
    verbose_name_plural = 'Observaciones'

@admin.register(RegistroAnestesia)
class RegistroAnestesiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'anestesiologo', 'fecha', 'sala')
    search_fields = ('paciente__numeroDocumento', 'anestesiologo__username')
    list_filter = ('fecha',)
    
    inlines = [
        EvaluacionInline,
        MonitoreoInline,
        VentilacionInline,
        MedicamentosInline,
        LiquidosInline,
        SignosVitalesInline,
        TecnicaInline,
        SalidaInline,
        ObservacionesInline
    ]
