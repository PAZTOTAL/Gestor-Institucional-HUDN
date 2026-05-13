from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    Geo01Pais, Geo02Departamento, Geo03Municipio,
    Geo04Ciudad, Geo05Comuna, ListaTipoDocumento, ListaTipoSexo
)

class GeoreferenciaDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal de Georeferencia con los 5 niveles (Estilo Organigrama)."""
    template_name = 'BasesGenerales/georeferencia_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pais_count'] = Geo01Pais.objects.count()
        context['depto_count'] = Geo02Departamento.objects.count()
        context['muni_count'] = Geo03Municipio.objects.count()
        context['ciudad_count'] = Geo04Ciudad.objects.count()
        context['comuna_count'] = Geo05Comuna.objects.count()
        context['tipodoc_count'] = ListaTipoDocumento.objects.count()
        context['sexo_count'] = ListaTipoSexo.objects.count()
        return context
