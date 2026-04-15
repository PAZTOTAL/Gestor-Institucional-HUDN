from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    Organigrama01, Organigrama02, Organigrama03,
    Organigrama04, Organigrama05, Organigrama06,
    doc_tabHonorarios, Supervisores,
)


class OrganigramaDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal del Organigrama Institucional con los 6 niveles."""
    template_name = 'A_00_Organigrama/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['n1_count'] = Organigrama01.objects.count()
        context['n2_count'] = Organigrama02.objects.count()
        context['n3_count'] = Organigrama03.objects.count()
        context['n4_count'] = Organigrama04.objects.count()
        context['n5_count'] = Organigrama05.objects.count()
        context['n6_count'] = Organigrama06.objects.count()
        context['honorarios_count'] = doc_tabHonorarios.objects.count()
        context['supervisores_count'] = Supervisores.objects.count()
        return context
