from django.contrib import admin
from .models import PacienteNeurocritico

@admin.register(PacienteNeurocritico)
class PacienteNeurocriticoAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'primer_nombre', 'primer_apellido', 'glasgow_ingreso', 'donante_efectivo')
    search_fields = ('numero_documento', 'primer_nombre', 'primer_apellido')
    list_filter = ('donante_efectivo', 'dx_muerte_encefalica', 'servicio')
