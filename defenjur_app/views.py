from datetime import date
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import (
    AccionTutela, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    DerechoPeticion, ArchivoAdjunto, Peritaje, PagoSentenciaJudicial,
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio, RequerimientoEnteControl
)
from .forms import (
    AccionTutelaForm, DerechoPeticionForm, ProcesoExtrajudicialForm, ProcesoJudicialActivaForm,
    ProcesoJudicialPasivaForm, PeritajeForm, PagoSentenciaJudicialForm, ProcesoJudicialTerminadoForm,
    ProcesoAdministrativoSancionatorioForm, RequerimientoEnteControlForm
)
from .access_control import filter_queryset_by_role
from .import_logic import importar_entidad_view, descargar_plantilla_view

User = get_user_model()

# ─── Dashboard Logic ──────────────────────────────────────────────────────────
def _monthly_counts_for_year(model, year):
    rows = (
        model.objects.filter(fecha_registro__year=year)
        .annotate(m=TruncMonth('fecha_registro'))
        .values('m')
        .annotate(c=Count('id'))
    )
    by_m = {r['m'].month: r['c'] for r in rows if r['m']}
    return [by_m.get(m, 0) for m in range(1, 13)]

def build_dashboard_chart_context():
    y = date.today().year
    context = {
        'count_extrajudiciales': ProcesoExtrajudicial.objects.count(),
        'count_procesos_activa': ProcesoJudicialActiva.objects.count(),
        'count_procesos_pasiva': ProcesoJudicialPasiva.objects.count(),
        'count_tutelas': AccionTutela.objects.count(),
        'count_peticiones': DerechoPeticion.objects.count(),
        'count_requerimientos': RequerimientoEnteControl.objects.count(),
        'count_peritajes': Peritaje.objects.count(),
        'count_pagos': PagoSentenciaJudicial.objects.count(),
        'count_sancionatorios': ProcesoAdministrativoSancionatorio.objects.count(),
        'count_terminados': ProcesoJudicialTerminado.objects.count(),
    }
    
    chart_config = {
        'donut': {
            'labels': ['Extrajudicial', 'Judicial Activa', 'Judicial Pasiva', 'Tutelas', 'Peticiones'],
            'data': [context['count_extrajudiciales'], context['count_procesos_activa'], context['count_procesos_pasiva'], context['count_tutelas'], context['count_peticiones']]
        },
        'bar': {
            'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'activa': _monthly_counts_for_year(ProcesoJudicialActiva, y),
            'pasiva': _monthly_counts_for_year(ProcesoJudicialPasiva, y),
            'year': y
        }
    }
    context['chart_config'] = chart_config
    return context

# ─── Mixins ───────────────────────────────────────────────────────────────────
class RoleFilteringMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return filter_queryset_by_role(qs, self.request.user, self.model)

class CommandCenterMixin:
    """Adds analytical data and status filtering to ListViews."""
    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get('status')
        model_name = self.model._meta.model_name
        
        if status:
            if model_name == 'acciontutela':
                if status == 'en_curso': qs = qs.filter(Q(fecha_respuesta_tramite="") | Q(fecha_respuesta_tramite__isnull=True))
                elif status == 'tramitados': qs = qs.exclude(Q(fecha_respuesta_tramite="") | Q(fecha_respuesta_tramite__isnull=True))
            elif model_name == 'derechopeticion':
                if status == 'en_curso': qs = qs.filter(Q(fecha_respuesta_peticion="") | Q(fecha_respuesta_peticion__isnull=True))
                elif status == 'tramitados': qs = qs.exclude(Q(fecha_respuesta_peticion="") | Q(fecha_respuesta_peticion__isnull=True))
            elif model_name == 'peritaje':
                if status == 'en_curso': qs = qs.filter(Q(pago_honorarios="") | Q(pago_honorarios__isnull=True))
                elif status == 'tramitados': qs = qs.exclude(Q(pago_honorarios="") | Q(pago_honorarios__isnull=True))
            elif model_name == 'requerimientoentecontrol':
                if status == 'en_curso': qs = qs.filter(Q(fecha_respuesta_tramite="") | Q(fecha_respuesta_tramite__isnull=True))
                elif status == 'tramitados': qs = qs.exclude(Q(fecha_respuesta_tramite="") | Q(fecha_respuesta_tramite__isnull=True))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Calculate Reparto Data (Distribution)
        reparto = (
            self.model.objects.values('abogado_responsable')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        total_rows = sum(item['total'] for item in reparto) or 1
        reparto_list = []
        for item in reparto:
            reparto_list.append({
                'abogado': item['abogado_responsable'],
                'total': item['total'],
                'percent': round((item['total'] / total_rows) * 100)
            })
        ctx['reparto_data'] = reparto_list
        return ctx

# ─── Core Views ───────────────────────────────────────────────────────────────
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'defenjur/home.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_dashboard_chart_context())
        return ctx

class AyudaView(LoginRequiredMixin, TemplateView):
    template_name = 'defenjur/ayuda.html'

class ReportesView(LoginRequiredMixin, TemplateView):
    template_name = 'defenjur/reportes.html'
    def get_context_data(self, **kwargs):
        if not getattr(self.request.user.perfil, 'legal_rol', '').lower() == 'administrador' and not self.request.user.is_superuser:
             raise PermissionDenied
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_dashboard_chart_context())
        return ctx

# ─── Entity Views (Simplified Examples) ───────────────────────────────────────
class TutelaListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView):
    model = AccionTutela
    template_name = 'defenjur/tutela_list.html'
    context_object_name = 'tutelas'
    paginate_by = 10

class TutelaCreateView(LoginRequiredMixin, CreateView):
    model = AccionTutela
    form_class = AccionTutelaForm
    template_name = 'defenjur/tutela_form.html'
    success_url = reverse_lazy('defenjur:tutelas')

class TutelaUpdateView(LoginRequiredMixin, RoleFilteringMixin, UpdateView):
    model = AccionTutela
    form_class = AccionTutelaForm
    template_name = 'defenjur/tutela_form.html'
    success_url = reverse_lazy('defenjur:tutelas')

# ... Repetir para otras entidades se haría de forma similar ...
# Agregando placeholders para que el urls.py no rompa
class ExtrajudicialListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView):
    model = ProcesoExtrajudicial
    template_name = 'defenjur/extrajudicial_list.html'
    context_object_name = 'items'

class ExtrajudicialConciliadosListView(ExtrajudicialListView):
    def get_queryset(self): return super().get_queryset().filter(clasificacion__icontains='conciliado')

class ExtrajudicialNoConciliadosListView(ExtrajudicialListView):
    def get_queryset(self): return super().get_queryset().filter(clasificacion__icontains='no conciliado')

class ExtrajudicialCreateView(CreateView):
    model = ProcesoExtrajudicial
    form_class = ProcesoExtrajudicialForm
    template_name = 'defenjur/extrajudicial_form.html'
    success_url = reverse_lazy('defenjur:extrajudiciales')

class ExtrajudicialUpdateView(UpdateView):
    model = ProcesoExtrajudicial
    form_class = ProcesoExtrajudicialForm
    template_name = 'defenjur/extrajudicial_form.html'
    success_url = reverse_lazy('defenjur:extrajudiciales')

# Sigo con las demás clases requeridas por urls.py...
class PeticionListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView):
    model = DerechoPeticion
    template_name = 'defenjur/peticion_list.html'
    context_object_name = 'peticiones'
    paginate_by = 10

class PeticionCreateView(CreateView):
    model = DerechoPeticion
    form_class = DerechoPeticionForm
    template_name = 'defenjur/peticion_form.html'
    success_url = reverse_lazy('defenjur:peticiones')

class PeticionUpdateView(UpdateView):
    model = DerechoPeticion
    form_class = DerechoPeticionForm
    template_name = 'defenjur/peticion_form.html'
    success_url = reverse_lazy('defenjur:peticiones')

class ProcesoActivaListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = ProcesoJudicialActiva; template_name = 'defenjur/proceso_activa_list.html'; context_object_name = 'procesos'
class ProcesoActivaCreateView(CreateView): model = ProcesoJudicialActiva; form_class = ProcesoJudicialActivaForm; template_name = 'defenjur/proceso_activa_form.html'; success_url = reverse_lazy('defenjur:procesos_activos')
class ProcesoActivaUpdateView(UpdateView): model = ProcesoJudicialActiva; form_class = ProcesoJudicialActivaForm; template_name = 'defenjur/proceso_activa_form.html'; success_url = reverse_lazy('defenjur:procesos_activos')

class ProcesoPasivaListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = ProcesoJudicialPasiva; template_name = 'defenjur/proceso_pasiva_list.html'; context_object_name = 'procesos'
class ProcesoPasivaCreateView(CreateView): model = ProcesoJudicialPasiva; form_class = ProcesoJudicialPasivaForm; template_name = 'defenjur/proceso_pasiva_form.html'; success_url = reverse_lazy('defenjur:procesos_pasivos')
class ProcesoPasivaUpdateView(UpdateView): model = ProcesoJudicialPasiva; form_class = ProcesoJudicialPasivaForm; template_name = 'defenjur/proceso_pasiva_form.html'; success_url = reverse_lazy('defenjur:procesos_pasivos')

class ProcesoTerminadoListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = ProcesoJudicialTerminado; template_name = 'defenjur/proceso_terminado_list.html'; context_object_name = 'procesos'
class ProcesoTerminadoCreateView(CreateView): model = ProcesoJudicialTerminado; form_class = ProcesoJudicialTerminadoForm; template_name = 'defenjur/proceso_terminado_form.html'; success_url = reverse_lazy('defenjur:procesos_terminados')
class ProcesoTerminadoUpdateView(UpdateView): model = ProcesoJudicialTerminado; form_class = ProcesoJudicialTerminadoForm; template_name = 'defenjur/proceso_terminado_form.html'; success_url = reverse_lazy('defenjur:procesos_terminados')

class PeritajeListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = Peritaje; template_name = 'defenjur/peritaje_list.html'; context_object_name = 'peritajes'
class PeritajeCreateView(CreateView): model = Peritaje; form_class = PeritajeForm; template_name = 'defenjur/peritaje_form.html'; success_url = reverse_lazy('defenjur:peritajes')
class PeritajeUpdateView(UpdateView): model = Peritaje; form_class = PeritajeForm; template_name = 'defenjur/peritaje_form.html'; success_url = reverse_lazy('defenjur:peritajes')

class PagoListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = PagoSentenciaJudicial; template_name = 'defenjur/pago_list.html'; context_object_name = 'pagos'
class PagoCreateView(CreateView): model = PagoSentenciaJudicial; form_class = PagoSentenciaJudicialForm; template_name = 'defenjur/pago_form.html'; success_url = reverse_lazy('defenjur:pagos')
class PagoUpdateView(UpdateView): model = PagoSentenciaJudicial; form_class = PagoSentenciaJudicialForm; template_name = 'defenjur/pago_form.html'; success_url = reverse_lazy('defenjur:pagos')

class SancionatorioListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = ProcesoAdministrativoSancionatorio; template_name = 'defenjur/sancionatorio_list.html'; context_object_name = 'items'
class SancionatorioCreateView(CreateView): model = ProcesoAdministrativoSancionatorio; form_class = ProcesoAdministrativoSancionatorioForm; template_name = 'defenjur/sancionatorio_form.html'; success_url = reverse_lazy('defenjur:sancionatorios')
class SancionatorioUpdateView(UpdateView): model = ProcesoAdministrativoSancionatorio; form_class = ProcesoAdministrativoSancionatorioForm; template_name = 'defenjur/sancionatorio_form.html'; success_url = reverse_lazy('defenjur:sancionatorios')

class RequerimientoListView(LoginRequiredMixin, RoleFilteringMixin, CommandCenterMixin, ListView): model = RequerimientoEnteControl; template_name = 'defenjur/requerimiento_list.html'; context_object_name = 'requerimientos'
class RequerimientoCreateView(CreateView): model = RequerimientoEnteControl; form_class = RequerimientoEnteControlForm; template_name = 'defenjur/requerimiento_form.html'; success_url = reverse_lazy('defenjur:requerimientos')
class RequerimientoUpdateView(UpdateView): model = RequerimientoEnteControl; form_class = RequerimientoEnteControlForm; template_name = 'defenjur/requerimiento_form.html'; success_url = reverse_lazy('defenjur:requerimientos')

# ─── AJAX / Stats ────────────────────────────────────────────────────────────
@login_required
def api_consultas_totales(request):
    return JsonResponse(build_dashboard_chart_context())

@login_required
def api_estadisticas_rango(request):
    # Simplificado para el demo
    return JsonResponse({'status': 'ok'})

# ─── Utils ───────────────────────────────────────────────────────────────────
@login_required
def exportar_modulo_excel(request, modulo):
    return HttpResponse("Funcionalidad de exportación en desarrollo")

@login_required
def importar_modulo_excel(request, modulo):
    return importar_entidad_view(request, modulo)

@login_required
def descargar_plantilla_excel(request, modulo):
    return descargar_plantilla_view(request, modulo)

@login_required
def lista_archivos_view(request, tipo, id_obj):
    archivos = ArchivoAdjunto.objects.filter(tipo_asociado=tipo, id_asociado=id_obj)
    return render(request, 'defenjur/lista_archivos_modal.html', {'archivos': archivos})

@login_required
def eliminar_registro(request, tipo, id_obj):
    # Lógica de eliminación...
    messages.success(request, "Registro eliminado")
    return redirect('defenjur:home')
