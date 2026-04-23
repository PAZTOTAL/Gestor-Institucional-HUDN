from django.contrib import admin
from .models import (
    EmpresaTercerizada, ContratoTercerizado, ActividadTercerizado,
    ServidorTercerizado, AsignacionOrganigrama, AfiliacionSeguridad
)


@admin.register(EmpresaTercerizada)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nit', 'razon_social', 'tipo_servicio', 'activa', 'fecha_registro']
    list_filter = ['activa', 'tipo_servicio']
    search_fields = ['nit', 'razon_social']


@admin.register(ContratoTercerizado)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['numero_contrato', 'empresa', 'estado', 'fecha_inicio', 'fecha_fin']
    list_filter = ['estado', 'empresa']
    search_fields = ['numero_contrato']


@admin.register(ActividadTercerizado)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']


class AfiliacionInline(admin.TabularInline):
    model = AfiliacionSeguridad
    extra = 0


class AsignacionInline(admin.TabularInline):
    model = AsignacionOrganigrama
    extra = 0
    fields = ['organigrama_nivel1', 'organigrama_nivel2', 'organigrama_nivel3',
              'actividad', 'fecha_inicio', 'fecha_fin', 'activa']


@admin.register(ServidorTercerizado)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'empresa', 'activo_hospital',
                    'en_dinamica', 'fecha_ingreso']
    list_filter = ['activo_hospital', 'en_dinamica', 'empresa']
    search_fields = ['numero_documento', 'primer_nombre', 'primer_apellido']
    inlines = [AsignacionInline, AfiliacionInline]

    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre Completo'


@admin.register(AsignacionOrganigrama)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'organigrama_nivel2', 'actividad', 'activa']
    list_filter = ['activa']


@admin.register(AfiliacionSeguridad)
class AfiliacionAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'tipo', 'nombre_entidad', 'vigente', 'fecha_vencimiento']
    list_filter = ['tipo', 'vigente']
