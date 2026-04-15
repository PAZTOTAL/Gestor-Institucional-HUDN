"""
Vistas Django alineadas con la lógica de defenjur-back/controllers (Node).

Mapeo resumido:
- consultas_generales.js → build_dashboard_chart_context() + api_consultas_totales
- users.js → UsuarioListView, UsuarioCreateView, UsuarioUpdateView, usuario_eliminar
- acciones_tutela.js (CRUD, getAllByUser, getByMonthYear, getByDateRange) → TutelaListView
  (RoleFilteringMixin ≈ getAllByUser), filtros fecha + api_estadisticas_rango modulo=acciones_tutela
- derechos_peticion, pagos_*, peritajes, requerimientos_*, proc_*, sancionatorios → CRUD en vistas
  + estadisticas_rango_por_modulo (node_parity) para getByDateRange
- Archivos: ArchivoAdjunto (MEDIA) + espejo opcional a FTP si DEFENJUR_FTP_ENABLED (ver settings).
- API JSON por entidad: legal/api_entities.py (getAll/getDetail).
"""
from datetime import date

from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .models import (
    AccionTutela, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    DerechoPeticion, ArchivoAdjunto, Peritaje, PagoSentenciaJudicial,
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio, RequerimientoEnteControl
)
from .forms import (
    AccionTutelaForm, DerechoPeticionForm, ProcesoExtrajudicialForm, ProcesoJudicialActivaForm,
    ProcesoJudicialPasivaForm, PeritajeForm, PagoSentenciaJudicialForm, ProcesoJudicialTerminadoForm,
    ProcesoAdministrativoSancionatorioForm, RequerimientoEnteControlForm,
    UsuarioHudnCreateForm, UsuarioHudnUpdateForm,
)
from .query_helpers import filter_charfield_dmy_range, filter_tutela_by_month_year, is_dmy_string
from .node_parity import estadisticas_rango_por_modulo

from .access_control import filter_queryset_by_role
from .excel_export import EXPORT_SLUGS, build_excel_response, get_export_queryset
from .ftp_service import mirror_archivo_adjunto_to_ftp


# ─── Helper ───────────────────────────────────────────────────────────────────
def _guardar_adjuntos(files, tipo, id_obj):
    for f in files:
        adj = ArchivoAdjunto.objects.create(
            tipo_asociado=tipo, id_asociado=id_obj,
            archivo=f, nombre_original=f.name
        )
        mirror_archivo_adjunto_to_ftp(tipo, id_obj, adj.archivo, adj.nombre_original)

from django.contrib.auth.decorators import login_required


Usuario = get_user_model()


def _is_app_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil', None)
    rol = (getattr(user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
    return rol == 'administrador'


class AdminRequiredMixin(LoginRequiredMixin):
    """Solo superusuario o rol administrador (módulo Usuarios / reportes sensibles)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _is_app_admin(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def _monthly_counts_for_year(model, year):
    rows = (
        model.objects.filter(fecha_registro__year=year)
        .annotate(m=TruncMonth('fecha_registro'))
        .values('m')
        .annotate(c=Count('id'))
    )
    by_m = {}
    for r in rows:
        if r['m']:
            by_m[r['m'].month] = r['c']
    return [by_m.get(m, 0) for m in range(1, 13)]


def build_dashboard_chart_context():
    """Datos para gráficos tipo sistema legacy (donut + barras mensuales)."""
    y = date.today().year
    c_ext = ProcesoExtrajudicial.objects.count()
    c_act = ProcesoJudicialActiva.objects.count()
    c_pas = ProcesoJudicialPasiva.objects.count()
    c_tut = AccionTutela.objects.count()
    c_pet = DerechoPeticion.objects.count()
    c_req = RequerimientoEnteControl.objects.count()
    c_per = Peritaje.objects.count()
    c_pag = PagoSentenciaJudicial.objects.count()
    c_san = ProcesoAdministrativoSancionatorio.objects.count()
    c_ter = ProcesoJudicialTerminado.objects.count()

    donut_labels = [
        'Proc. extrajudiciales', 'Proc. jud. activa', 'Proc. jud. pasiva', 'Tutelas',
        'Derechos de petición', 'Req. entes control', 'Peritajes',
        'Pagos sentencias judiciales',
        'Proc. adm. sancionatorios',
    ]
    donut_data = [c_ext, c_act, c_pas, c_tut, c_pet, c_req, c_per, c_pag, c_san]

    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    bar_activa = _monthly_counts_for_year(ProcesoJudicialActiva, y)
    bar_pasiva = _monthly_counts_for_year(ProcesoJudicialPasiva, y)

    chart_config = {
        'donut': {'labels': donut_labels, 'data': donut_data},
        'bar': {'labels': meses, 'activa': bar_activa, 'pasiva': bar_pasiva, 'year': y},
    }
    return {
        'count_extrajudiciales': c_ext,
        'count_procesos_activa': c_act,
        'count_procesos_pasiva': c_pas,
        'count_tutelas': c_tut,
        'count_peticiones': c_pet,
        'count_requerimientos': c_req,
        'count_peritajes': c_per,
        'count_pagos': c_pag,
        'count_sancionatorios': c_san,
        'count_terminados': c_ter,
        'chart_config': chart_config,
        'chart_year': y,
    }


class RoleFilteringMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return filter_queryset_by_role(qs, self.request.user, self.model)


class SearchMixin:
    """Filtro de búsqueda por texto (parámetro GET `q`) sobre campos configurables."""
    search_param = 'q'
    search_fields = ()

    def get_queryset(self):
        qs = super().get_queryset()
        term = self.request.GET.get(self.search_param, '').strip()
        if not term or not self.search_fields:
            return qs
        cond = Q()
        for field in self.search_fields:
            cond |= Q(**{f'{field}__icontains': term})
        return qs.filter(cond)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_query'] = self.request.GET.get(self.search_param, '').strip()
        q = self.request.GET.copy()
        q.pop('page', None)
        ctx['filter_query'] = q.urlencode()
        return ctx

MODEL_TO_TIPO_ADJUNTO = {
    AccionTutela: 'tutela',
    DerechoPeticion: 'peticion',
    ProcesoJudicialActiva: 'proceso_activo',
    ProcesoJudicialPasiva: 'proceso_pasivo',
    ProcesoJudicialTerminado: 'proceso_terminado',
    Peritaje: 'peritaje',
    PagoSentenciaJudicial: 'pago',
    ProcesoAdministrativoSancionatorio: 'sancionatorio',
    RequerimientoEnteControl: 'requerimiento',
    ProcesoExtrajudicial: 'extrajudicial',
}


class ModalUpdateView(LoginRequiredMixin, RoleFilteringMixin, UpdateView):
    template_name = 'legal/form_modal.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_update'] = True
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        tipo = MODEL_TO_TIPO_ADJUNTO.get(type(self.object))
        if tipo:
            archivos = self.request.FILES.getlist('adjuntos')
            if archivos:
                _guardar_adjuntos(archivos, tipo, self.object.pk)
        return render(self.request, self.template_name, {'success': True})

@login_required
def lista_archivos_view(request, tipo, id_obj):
    archivos = ArchivoAdjunto.objects.filter(tipo_asociado=tipo, id_asociado=id_obj).order_by('-fecha_carga')
    return render(request, 'legal/lista_archivos_modal.html', {'archivos': archivos})

# ─── Dashboard ────────────────────────────────────────────────────────────────
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'legal/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_dashboard_chart_context())
        context['count_procesos'] = context['count_procesos_activa'] + context['count_procesos_pasiva']
        return context


class ReportesView(AdminRequiredMixin, TemplateView):
    """Consolidado de indicadores y gráficos (equivalente a menú Reportes del sistema legacy)."""
    template_name = 'legal/reportes.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_dashboard_chart_context())
        return ctx


class UsuarioListView(AdminRequiredMixin, ListView):
    model = Usuario
    template_name = 'legal/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 25
    ordering = ['username']

    def get_queryset(self):
        return Usuario.objects.all().order_by('username')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.copy()
        q.pop('page', None)
        ctx['filter_query'] = q.urlencode()
        return ctx


class UsuarioCreateView(AdminRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioHudnCreateForm
    template_name = 'legal/usuario_form.html'
    success_url = reverse_lazy('usuarios')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado correctamente.')
        return super().form_valid(form)


class UsuarioUpdateView(AdminRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioHudnUpdateForm
    template_name = 'legal/usuario_form.html'
    success_url = reverse_lazy('usuarios')

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente.')
        return super().form_valid(form)


# ─── Tutelas ──────────────────────────────────────────────────────────────────
class TutelaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = AccionTutela
    template_name = 'legal/tutela_list.html'
    context_object_name = 'tutelas'
    paginate_by = 10
    search_fields = (
        'accionante', 'identificacion_accionante', 'num_proceso', 'despacho_judicial',
        'abogado_responsable', 'tipo_tramite', 'observaciones',
    )

    def get_queryset(self):
        qs = super().get_queryset()
        mes = self.request.GET.get('mes', '').strip()
        anio = self.request.GET.get('anio', '').strip()
        if mes.isdigit() and anio.isdigit():
            qs = filter_tutela_by_month_year(qs, int(mes), int(anio))

        fd = self.request.GET.get('fecha_desde', '').strip()
        fh = self.request.GET.get('fecha_hasta', '').strip()
        if fd and fh and is_dmy_string(fd) and is_dmy_string(fh):
            qs = filter_charfield_dmy_range(qs, 'fecha_llegada', fd, fh)
        else:
            if fd:
                qs = qs.filter(fecha_llegada__icontains=fd)
            if fh:
                qs = qs.filter(fecha_llegada__icontains=fh)
        return qs

    def get_paginate_by(self, queryset):
        pp = str(self.request.GET.get('per_page', '10'))
        allowed = {'5': 5, '10': 10, '25': 25, '50': 50, '100': 100}
        return allowed.get(pp, 10)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        ctx['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        ctx['mes'] = self.request.GET.get('mes', '')
        ctx['anio'] = self.request.GET.get('anio', '')
        ctx['per_page_sel'] = str(self.request.GET.get('per_page', '10'))
        return ctx

class TutelaCreateView(LoginRequiredMixin, CreateView):
    model = AccionTutela
    form_class = AccionTutelaForm
    template_name = 'legal/tutela_form.html'
    success_url = reverse_lazy('tutelas')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'tutela', self.object.id)
        messages.success(self.request, 'Acción de Tutela registrada correctamente.')
        return response

class TutelaUpdateView(ModalUpdateView):
    model = AccionTutela
    form_class = AccionTutelaForm


# ─── Derechos de Petición ─────────────────────────────────────────────────────
class PeticionListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = DerechoPeticion
    template_name = 'legal/peticion_list.html'
    context_object_name = 'peticiones'
    paginate_by = 10
    search_fields = (
        'num_reparto', 'fecha_correo', 'nombre_persona_solicitante', 'peticionario',
        'causa_peticion', 'abogado_responsable', 'cedula_persona_solicitante',
        'num_rad_interno',
    )

class PeticionCreateView(LoginRequiredMixin, CreateView):
    model = DerechoPeticion
    form_class = DerechoPeticionForm
    template_name = 'legal/peticion_form.html'
    success_url = reverse_lazy('peticiones')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'peticion', self.object.id)
        messages.success(self.request, 'Derecho de Petición registrado correctamente.')
        return response

class PeticionUpdateView(ModalUpdateView):
    model = DerechoPeticion
    form_class = DerechoPeticionForm


# ─── Procesos Judiciales ──────────────────────────────────────────────────────
class ProcesoActivaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = ProcesoJudicialActiva
    template_name = 'legal/proceso_activa_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    )

class ProcesoActivaCreateView(LoginRequiredMixin, CreateView):
    model = ProcesoJudicialActiva
    form_class = ProcesoJudicialActivaForm
    template_name = 'legal/proceso_activa_form.html'
    success_url = reverse_lazy('procesos_activos')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'proceso_activo', self.object.id)
        messages.success(self.request, 'Proceso Judicial Activo registrado correctamente.')
        return response

class ProcesoActivaUpdateView(ModalUpdateView):
    model = ProcesoJudicialActiva
    form_class = ProcesoJudicialActivaForm


class ProcesoPasivaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = ProcesoJudicialPasiva
    template_name = 'legal/proceso_pasiva_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
        'medio_control',
    )

class ProcesoPasivaCreateView(LoginRequiredMixin, CreateView):
    model = ProcesoJudicialPasiva
    form_class = ProcesoJudicialPasivaForm
    template_name = 'legal/proceso_pasiva_form.html'
    success_url = reverse_lazy('procesos_pasivos')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'proceso_pasivo', self.object.id)
        messages.success(self.request, 'Proceso Judicial Pasivo registrado correctamente.')
        return response

class ProcesoPasivaUpdateView(ModalUpdateView):
    model = ProcesoJudicialPasiva
    form_class = ProcesoJudicialPasivaForm


class ProcesoTerminadoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = ProcesoJudicialTerminado
    template_name = 'legal/proceso_terminado_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual', 'medio_control',
    )

class ProcesoTerminadoCreateView(LoginRequiredMixin, CreateView):
    model = ProcesoJudicialTerminado
    form_class = ProcesoJudicialTerminadoForm
    template_name = 'legal/proceso_terminado_form.html'
    success_url = reverse_lazy('procesos_terminados')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'proceso_terminado', self.object.id)
        messages.success(self.request, 'Proceso Judicial Terminado registrado correctamente.')
        return response

class ProcesoTerminadoUpdateView(ModalUpdateView):
    model = ProcesoJudicialTerminado
    form_class = ProcesoJudicialTerminadoForm


# ─── Peritajes ────────────────────────────────────────────────────────────────
class PeritajeListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = Peritaje
    template_name = 'legal/peritaje_list.html'
    context_object_name = 'peritajes'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
        'demandante', 'demandado', 'abogado_responsable', 'perito_asignado', 'asunto', 'num_reparto',
    )

class PeritajeCreateView(LoginRequiredMixin, CreateView):
    model = Peritaje
    form_class = PeritajeForm
    template_name = 'legal/peritaje_form.html'
    success_url = reverse_lazy('peritajes')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'peritaje', self.object.id)
        messages.success(self.request, 'Peritaje registrado correctamente.')
        return response

class PeritajeUpdateView(ModalUpdateView):
    model = Peritaje
    form_class = PeritajeForm


# ─── Pagos de Sentencias ──────────────────────────────────────────────────────
class PagoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = PagoSentenciaJudicial
    template_name = 'legal/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_pago', 'despacho_tramitante', 'medio_control',
        'demandante', 'demandado', 'abogado_responsable', 'valor_pagado', 'estado', 'tipo_pago',
    )

class PagoCreateView(LoginRequiredMixin, CreateView):
    model = PagoSentenciaJudicial
    form_class = PagoSentenciaJudicialForm
    template_name = 'legal/pago_form.html'
    success_url = reverse_lazy('pagos')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'pago', self.object.id)
        messages.success(self.request, 'Pago de Sentencia registrado correctamente.')
        return response

class PagoUpdateView(ModalUpdateView):
    model = PagoSentenciaJudicial
    form_class = PagoSentenciaJudicialForm


# ─── Proc. Adm. Sancionatorios ────────────────────────────────────────────────
class SancionatorioListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = ProcesoAdministrativoSancionatorio
    template_name = 'legal/sancionatorio_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_requerimiento', 'entidad', 'causa', 'estado',
        'entidad_solicitante_requerimiento', 'objeto_requerimiento',
    )

class SancionatorioCreateView(LoginRequiredMixin, CreateView):
    model = ProcesoAdministrativoSancionatorio
    form_class = ProcesoAdministrativoSancionatorioForm
    template_name = 'legal/sancionatorio_form.html'
    success_url = reverse_lazy('sancionatorios')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'sancionatorio', self.object.id)
        messages.success(self.request, 'Proceso Administrativo Sancionatorio registrado.')
        return response

class SancionatorioUpdateView(ModalUpdateView):
    model = ProcesoAdministrativoSancionatorio
    form_class = ProcesoAdministrativoSancionatorioForm


# ─── Requerimientos Entes de Control ─────────────────────────────────────────
class RequerimientoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = RequerimientoEnteControl
    template_name = 'legal/requerimiento_list.html'
    context_object_name = 'requerimientos'
    paginate_by = 10
    search_fields = (
        'num_reparto', 'num_proceso', 'fecha_correo_electronico',
        'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable', 'tipo_tramite',
    )

class RequerimientoCreateView(LoginRequiredMixin, CreateView):
    model = RequerimientoEnteControl
    form_class = RequerimientoEnteControlForm
    template_name = 'legal/requerimiento_form.html'
    success_url = reverse_lazy('requerimientos')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'requerimiento', self.object.id)
        messages.success(self.request, 'Requerimiento de Ente de Control registrado.')
        return response

class RequerimientoUpdateView(ModalUpdateView):
    model = RequerimientoEnteControl
    form_class = RequerimientoEnteControlForm


@login_required
@require_http_methods(['DELETE'])
def eliminar_registro(request, tipo, id_obj):
    # Validar permisos en una app real, pero por ahora como admin está bien.
    mapa = {
        'peticion': DerechoPeticion,
        'tutela': AccionTutela,
        'proceso_activo': ProcesoJudicialActiva,
        'proceso_pasivo': ProcesoJudicialPasiva,
        'proceso_terminado': ProcesoJudicialTerminado,
        'peritaje': Peritaje,
        'pago': PagoSentenciaJudicial,
        'sancionatorio': ProcesoAdministrativoSancionatorio,
        'requerimiento': RequerimientoEnteControl,
        'extrajudicial': ProcesoExtrajudicial,
    }
    modelo = mapa.get(tipo)
    if modelo:
        obj = get_object_or_404(modelo, id=id_obj)
        # Opcional: Validar si es abogado, solo puede borrar lo suyo.
        obj.delete()
        return HttpResponse('') # HTMX vacía el TR
    return HttpResponse('Error', status=400)

class ExtrajudicialListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, ListView):
    model = ProcesoExtrajudicial
    template_name = 'legal/extrajudicial_list.html'
    context_object_name = 'extrajudiciales'
    paginate_by = 10
    search_fields = (
        'demandante', 'demandado', 'apoderado', 'medio_control', 'despacho_conocimiento', 'estado', 'clasificacion',
    )
    extrajudicial_filtro = 'todos'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['extrajudicial_filtro'] = self.extrajudicial_filtro
        if self.extrajudicial_filtro == 'conciliados':
            ctx['excel_export_modulo'] = 'extrajudiciales_conciliados'
        elif self.extrajudicial_filtro == 'no_conciliados':
            ctx['excel_export_modulo'] = 'extrajudiciales_no_conciliados'
        else:
            ctx['excel_export_modulo'] = 'extrajudiciales'
        return ctx


class ExtrajudicialConciliadosListView(ExtrajudicialListView):
    extrajudicial_filtro = 'conciliados'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            Q(clasificacion__icontains='conciliado') & ~Q(clasificacion__icontains='no concili')
        )


class ExtrajudicialNoConciliadosListView(ExtrajudicialListView):
    extrajudicial_filtro = 'no_conciliados'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            Q(clasificacion__icontains='no concili')
            | Q(clasificacion__isnull=True)
            | Q(clasificacion='')
        )

class ExtrajudicialCreateView(LoginRequiredMixin, CreateView):
    model = ProcesoExtrajudicial
    form_class = ProcesoExtrajudicialForm
    template_name = 'legal/extrajudicial_form.html'
    success_url = reverse_lazy('extrajudiciales')

    def form_valid(self, form):
        response = super().form_valid(form)
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'extrajudicial', self.object.pk)
        messages.success(self.request, 'Proceso extrajudicial registrado correctamente.')
        return response


class ExtrajudicialUpdateView(ModalUpdateView):
    model = ProcesoExtrajudicial
    form_class = ProcesoExtrajudicialForm


class AyudaView(LoginRequiredMixin, TemplateView):
    template_name = 'legal/ayuda.html'


@login_required
@require_GET
def exportar_modulo_excel(request, modulo):
    """Descarga .xlsx del listado (mismos filtros GET: q, fechas, etc.)."""
    if modulo not in EXPORT_SLUGS:
        raise Http404
    if modulo == 'usuarios' and not _is_app_admin(request.user):
        raise PermissionDenied
    model, qs = get_export_queryset(modulo, request.user, request.GET)
    if model is None:
        raise Http404
    return build_excel_response(modulo, qs, model)


@login_required
@require_GET
def api_consultas_totales(request):
    """Igual que consultas_generales.js → total (conteos por tabla)."""
    ctx = build_dashboard_chart_context()
    return JsonResponse({
        'total_acciones_tutela': ctx['count_tutelas'],
        'derechos_peticion': ctx['count_peticiones'],
        'pagos_sentencias_judiciales': ctx['count_pagos'],
        'peritajes': ctx['count_peritajes'],
        'procesos_administrativos_sancionatorios': ctx['count_sancionatorios'],
        'procs_extrajudiciales': ctx['count_extrajudiciales'],
        'procs_judiciales_activa': ctx['count_procesos_activa'],
        'procs_judiciales_pasiva': ctx['count_procesos_pasiva'],
        'procs_judiciales_terminados': ctx['count_terminados'],
        'requerimientos_entes_control': ctx['count_requerimientos'],
    })


@login_required
@require_GET
def api_estadisticas_rango(request):
    """
    Paridad con getByDateRange de los controllers Node.
    GET: modulo, fechaInicio, fechaFin, tipoBusqueda (opcional), filtros por módulo.
    """
    body, err = estadisticas_rango_por_modulo(request.GET)
    if err:
        return JsonResponse(err, status=400)
    return JsonResponse(body)


@login_required
@require_POST
def usuario_eliminar(request, pk):
    if not _is_app_admin(request.user):
        raise PermissionDenied
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puede eliminar su propia cuenta.')
        return redirect('usuarios')
    usuario.delete()
    messages.success(request, 'Usuario eliminado correctamente.')
    return redirect('usuarios')


def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)
