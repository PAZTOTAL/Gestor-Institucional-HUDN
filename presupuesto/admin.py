from django.contrib import admin
from .models import CDP, RP

@admin.register(CDP)
class CDPAdmin(admin.ModelAdmin):
    list_display = ('cdp_numero', 'fecha', 'valor', 'tercero', 'rubro', 'nombre_rubro')
    search_fields = ('cdp_numero', 'objeto', 'rubro', 'nombre_rubro')
    list_filter = ('fecha',)

@admin.register(RP)
class RPAdmin(admin.ModelAdmin):
    list_display = ('rp_numero', 'cdp', 'fecha', 'valor', 'tercero')
    search_fields = ('rp_numero', 'objeto', 'otros_datos')
    list_filter = ('fecha',)
