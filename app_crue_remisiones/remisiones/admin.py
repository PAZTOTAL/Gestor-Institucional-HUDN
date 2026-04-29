from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Remision, UsuarioCrue


@admin.register(UsuarioCrue)
class UsuarioCrueAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'rol', 'is_active')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    # Extend the default UserAdmin fieldsets to include 'perfil'
    fieldsets = UserAdmin.fieldsets + (
        ('Rol CRUE', {'fields': ('rol',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rol CRUE', {'fields': ('rol',)}),
    )


@admin.register(Remision)
class RemisionAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'nombre', 'doc', 'tipo_doc', 'aceptado', 'created_by')
    list_filter = ('aceptado', 'tipo_doc', 'sexo', 'especialidad')
    search_fields = ('nombre', 'doc')
    date_hierarchy = 'fecha'
    readonly_fields = ('created_at', 'updated_at', 'created_by')
