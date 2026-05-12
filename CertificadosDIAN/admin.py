from django.contrib import admin
from .models import SolicitudCertificadoEmail, DatosCertificadoDIAN, RegistroDescargaCertificado

@admin.register(SolicitudCertificadoEmail)
class SolicitudCertificadoEmailAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cedula_consultada', 'nombre_empleado', 'email_envio', 'fecha_solicitud', 'procesado')
    list_filter = ('procesado', 'fecha_solicitud')
    search_fields = ('cedula_consultada', 'nombre_empleado', 'email_envio')

@admin.register(DatosCertificadoDIAN)
class DatosCertificadoDIANAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'primer_apellido', 'primer_nombre', 'anio_gravable')
    search_fields = ('cedula', 'primer_apellido', 'primer_nombre')

@admin.register(RegistroDescargaCertificado)
class RegistroDescargaCertificadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cedula_consultada', 'fecha_descarga', 'ip_descarga')
