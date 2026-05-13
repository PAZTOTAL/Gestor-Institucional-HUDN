from django.contrib import admin
from .models import DatosCertificadoDIAN, RegistroDescargaCertificado, SolicitudCertificadoEmail


@admin.register(RegistroDescargaCertificado)
class RegistroDescargaAdmin(admin.ModelAdmin):
    list_display = ('fecha_descarga', 'usuario', 'cedula_consultada', 'nombre_empleado', 'anio_gravable', 'ip_descarga')
    list_filter  = ('anio_gravable', 'fecha_descarga', 'usuario')
    search_fields = ('cedula_consultada', 'nombre_empleado', 'usuario__username', 'usuario__first_name', 'usuario__last_name', 'ip_descarga')
    readonly_fields = ('fecha_descarga', 'usuario', 'cedula_consultada', 'nombre_empleado', 'anio_gravable', 'ip_descarga', 'user_agent')
    ordering = ('-fecha_descarga',)
    date_hierarchy = 'fecha_descarga'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DatosCertificadoDIAN)
class DatosCertificadoDIANAdmin(admin.ModelAdmin):
    list_display  = ('cedula', 'primer_apellido', 'primer_nombre', 'anio_gravable')
    search_fields = ('cedula', 'primer_apellido', 'primer_nombre')
    list_filter   = ('anio_gravable',)


@admin.register(SolicitudCertificadoEmail)
class SolicitudCertificadoEmailAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'cedula_consultada', 'nombre_empleado', 'email_envio', 'fecha_solicitud', 'procesado')
    list_filter   = ('procesado', 'fecha_solicitud')
    search_fields = ('cedula_consultada', 'nombre_empleado', 'email_envio')
