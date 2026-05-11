from django.contrib import admin

from .models import Remision


@admin.register(Remision)
class RemisionAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'nombre', 'doc', 'tipo_doc', 'aceptado', 'created_by')
    list_filter = ('aceptado', 'tipo_doc', 'sexo', 'especialidad')
    search_fields = ('nombre', 'doc')
    date_hierarchy = 'fecha'
    readonly_fields = ('created_at', 'updated_at', 'created_by')
