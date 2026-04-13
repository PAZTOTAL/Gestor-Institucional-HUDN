from django.contrib import admin
from .models import ConsentimientoTemplate, ConsentimientoRegistro

@admin.register(ConsentimientoTemplate)
class ConsentimientoTemplateAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    search_fields = ('nombre',)

@admin.register(ConsentimientoRegistro)
class ConsentimientoRegistroAdmin(admin.ModelAdmin):
    list_display = ('template', 'paciente_oid', 'fecha_firma')
    list_filter = ('template', 'fecha_firma')
    search_fields = ('paciente_oid',)
