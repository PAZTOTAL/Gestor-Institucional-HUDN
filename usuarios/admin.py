from django.contrib import admin
from .models import PerfilUsuario, PermisoApp, PermisoModelo

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('user__username',)

@admin.register(PermisoApp)
class PermisoAppAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_label', 'permitido')
    list_filter = ('app_label', 'permitido')
    search_fields = ('user__username', 'app_label')

@admin.register(PermisoModelo)
class PermisoModeloAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_label', 'model_name', 'permitido')
    list_filter = ('app_label', 'model_name', 'permitido')
    search_fields = ('user__username', 'app_label', 'model_name')
