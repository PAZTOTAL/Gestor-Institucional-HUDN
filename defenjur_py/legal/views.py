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
import logging

logger = logging.getLogger(__name__)

from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse, Http404
from django.db import connections
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .models import (
    AccionTutela, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    DerechoPeticion, ArchivoAdjunto, Peritaje, PagoSentenciaJudicial,
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio, RequerimientoEnteControl,
    DespachoJudicial
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
        q.pop('sort', None)
        q.pop('dir', None)
        ctx['filter_query'] = q.urlencode()
        return ctx


class SortMixin:
    """
    Ordenamiento de columnas via parámetros GET: ?sort=<campo>&dir=asc|desc
    Las subclases deben definir `sort_allowed_fields` como dict:
        { 'alias_url': 'campo_db' }
    Por ejemplo: {'num_proceso': 'num_proceso', 'fecha': 'fecha_llegada'}
    """
    sort_allowed_fields = {}
    sort_default_field = 'id'
    sort_default_dir = 'desc'

    def _get_sort_params(self):
        sort_alias = self.request.GET.get('sort', '').strip()
        sort_dir = self.request.GET.get('dir', self.sort_default_dir).strip().lower()
        if sort_dir not in ('asc', 'desc'):
            sort_dir = self.sort_default_dir
        db_field = self.sort_allowed_fields.get(sort_alias, self.sort_default_field)
        return sort_alias or self.sort_default_field, sort_dir, db_field

    def get_queryset(self):
        qs = super().get_queryset()
        sort_alias, sort_dir, db_field = self._get_sort_params()
        prefix = '-' if sort_dir == 'desc' else ''
        return qs.order_by(f'{prefix}{db_field}')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sort_alias, sort_dir, _ = self._get_sort_params()
        ctx['sort_field'] = sort_alias
        ctx['sort_dir'] = sort_dir
        # filter_query sin sort/dir para que los links de th los regeneren limpios
        q = self.request.GET.copy()
        q.pop('sort', None)
        q.pop('dir', None)
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
    """
    Lista archivos de la DB y también escanea la NAS para archivos 'históricos'
    que no estén registrados en la tabla ArchivoAdjunto.
    """
    from .ftp_service import _ftp_config, FTP_ENTITY_FOLDER
    from ftplib import FTP
    
    # 1. Archivos en DB
    archivos_db = list(ArchivoAdjunto.objects.filter(tipo_asociado=tipo, id_asociado=id_obj).order_by('-fecha_carga'))
    nombres_en_db = {a.nombre_original for a in archivos_db}
    
    # 2. Escaneo de NAS para archivos históricos
    cfg = _ftp_config()
    folder = FTP_ENTITY_FOLDER.get(tipo)
    archivos_nas = []
    
    if cfg['enabled'] and cfg['host'] and folder:
        try:
            # Probar múltiples combinaciones de carpetas históricas
            # El usuario mencionó prefijo 2 para tutelas (168 -> 2168, 18 -> 218)
            # También hemos detectado carpetas con prefijo 3 y carpetas directas.
            prefijos = ['', '2', '3', '1']
            
            with FTP() as ftp:
                ftp.encoding = 'latin-1' # Para soportar eñes y tildes en servidores NAS antiguos
                ftp.connect(cfg['host'], timeout=10)
                ftp.login(cfg['user'], cfg['password'])
                
                for pref in prefijos:
                    remote_dir = f"{cfg['base_path']}/{folder}/{pref}{id_obj}"
                    try:
                        ftp.cwd(remote_dir)
                        files = ftp.nlst()
                        for f in files:
                            fname = f.split('/')[-1]
                            if not fname or fname in ['.', '..']: continue
                            
                            # Asegurar que el nombre del archivo se visualice bien en UTF-8
                            try:
                                # Si viene en latin-1 pero Python lo leyó raro
                                display_name = fname.encode('latin-1').decode('utf-8')
                            except:
                                display_name = fname

                            if display_name not in nombres_en_db and display_name not in {x['nombre'] for x in archivos_nas}:
                                archivos_nas.append({
                                    'id': None,
                                    'nombre': display_name,
                                    'es_historico': True,
                                    'url': f"/defenjur/adjunto/legacy/{tipo}/{id_obj}/{pref}/{fname}" 
                                })
                    except:
                        continue
        except Exception as e:
            logger.warning("Fallo escaneo NAS para lista: %s", e)

    return render(request, 'legal/lista_archivos_modal.html', {
        'archivos': archivos_db,
        'archivos_nas': archivos_nas,
        'tipo': tipo,
        'id_obj': id_obj
    })

@login_required
def descargar_adjunto_legacy_view(request, tipo, id_obj, pref, filename):
    """
    Descarga archivos que solo existen en la NAS (sin registro en DB).
    """
    from .ftp_service import _ftp_config, FTP_ENTITY_FOLDER
    from ftplib import FTP
    import io

    cfg = _ftp_config()
    folder = FTP_ENTITY_FOLDER.get(tipo)
    if not cfg['enabled'] or not folder:
        raise Http404

    try:
        remote_dir = f"{cfg['base_path']}/{folder}/{pref}{id_obj}"
        out = io.BytesIO()
        with FTP() as ftp:
            ftp.encoding = 'latin-1'
            ftp.connect(cfg['host'], timeout=15)
            ftp.login(cfg['user'], cfg['password'])
            ftp.cwd(remote_dir)
            ftp.retrbinary(f'RETR {filename}', out.write)
        
        out.seek(0)
        response = HttpResponse(out.read(), content_type="application/octet-stream")
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        logger.error("Error descarga legacy %s: %s", filename, e)
        raise Http404("Archivo no encontrado en la NAS.")

@login_required
def descargar_adjunto_smart_view(request, pk):
    """
    Intenta servir desde MEDIA local. Si no existe, intenta bajarlo de la NAS (FTP).
    """
    from .ftp_service import _ftp_config, _navigate_to_remote_dir, FTP_ENTITY_FOLDER
    from ftplib import FTP
    import os

    adjunto = get_object_or_404(ArchivoAdjunto, pk=pk)
    path_local = getattr(adjunto.archivo, 'path', None)
    
    # 1. Intentar local
    if path_local and os.path.exists(path_local):
        with open(path_local, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'inline; filename="{adjunto.nombre_original}"'
            return response

    # 2. Intentar NAS vía FTP
    cfg = _ftp_config()
    folder = FTP_ENTITY_FOLDER.get(adjunto.tipo_asociado)
    if cfg['enabled'] and cfg['host'] and folder:
        try:
            remote_dir = f"{cfg['base_path']}/{folder}/2{adjunto.id_asociado}"
            import io
            out = io.BytesIO()
            with FTP() as ftp:
                ftp.encoding = 'latin-1'
                ftp.connect(cfg['host'], timeout=10)
                ftp.login(cfg['user'], cfg['password'])
                ftp.cwd(remote_dir)
                ftp.retrbinary(f'RETR {adjunto.nombre_original}', out.write)
            
            out.seek(0)
            response = HttpResponse(out.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'inline; filename="{adjunto.nombre_original}"'
            return response
        except Exception as e:
            logger.warning("Fallo descarga desde NAS para PK %s: %s", pk, e)

    raise Http404("El archivo no se encuentra en el servidor local ni en la NAS.")

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
class TutelaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = AccionTutela
    template_name = 'legal/tutela_list.html'
    context_object_name = 'tutelas'
    paginate_by = 10
    search_fields = (
        'accionante', 'num_proceso', 'despacho_judicial',
        'abogado_responsable'
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'fecha': 'fecha_llegada',
        'despacho': 'despacho_judicial',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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

        abogado = self.request.GET.get('abogado', '').strip()
        if abogado:
            qs = qs.filter(abogado_responsable=abogado)

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
        
        # Lista única de abogados normalizada (Mayúsculas)
        from django.db.models.functions import Upper
        ctx['lista_abogados'] = AccionTutela.objects.annotate(
            nombre_up=Upper('abogado_responsable')
        ).exclude(
            nombre_up__isnull=True
        ).exclude(
            nombre_up=''
        ).exclude(
            nombre_up__icontains='AUDITORIA' # Filtrar ruidos
        ).values_list('nombre_up', flat=True).distinct().order_by('nombre_up')
        
        ctx['abogado_filter'] = self.request.GET.get('abogado', '')
        return ctx

class TutelaCreateView(LoginRequiredMixin, CreateView):
    model = AccionTutela
    form_class = AccionTutelaForm
    template_name = 'legal/tutela_form.html'
    success_url = reverse_lazy('tutelas')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.usuario_carga = self.request.user.get_username()
        obj.save()
        _guardar_adjuntos(self.request.FILES.getlist('adjuntos'), 'tutela', obj.id)
        messages.success(self.request, 'Acción de Tutela registrada correctamente.')
        return redirect(self.success_url)

class TutelaUpdateView(ModalUpdateView):
    model = AccionTutela
    form_class = AccionTutelaForm


# ─── Derechos de Petición ─────────────────────────────────────────────────────
class PeticionListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = DerechoPeticion
    template_name = 'legal/peticion_list.html'
    context_object_name = 'peticiones'
    paginate_by = 10
    search_fields = (
        'num_reparto', 'fecha_correo', 'nombre_persona_solicitante', 'peticionario',
        'causa_peticion', 'abogado_responsable', 'cedula_persona_solicitante',
        'num_rad_interno',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_reparto': 'num_reparto',
        'fecha': 'fecha_correo',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

    def get_queryset(self):
        qs = super().get_queryset()
        abogado = self.request.GET.get('abogado', '').strip()
        if abogado:
            qs = qs.filter(abogado_responsable=abogado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models.functions import Upper
        ctx['lista_abogados'] = DerechoPeticion.objects.annotate(
            nombre_up=Upper('abogado_responsable')
        ).exclude(
            nombre_up__isnull=True
        ).exclude(
            nombre_up=''
        ).exclude(
            nombre_up__icontains='AUDITORIA'
        ).values_list('nombre_up', flat=True).distinct().order_by('nombre_up')
        ctx['abogado_filter'] = self.request.GET.get('abogado', '')
        ctx['per_page_sel'] = str(self.request.GET.get('per_page', '10'))
        return ctx

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
class ProcesoActivaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = ProcesoJudicialActiva
    template_name = 'legal/proceso_activa_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual', 'medio_control',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'despacho': 'despacho_actual',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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


class ProcesoPasivaListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = ProcesoJudicialPasiva
    template_name = 'legal/proceso_pasiva_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual',
        'medio_control',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'despacho': 'despacho_actual',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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


class ProcesoTerminadoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = ProcesoJudicialTerminado
    template_name = 'legal/proceso_terminado_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'demandante', 'demandado', 'cc_demandante', 'apoderado', 'despacho_actual', 'medio_control',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'despacho': 'despacho_actual',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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
class PeritajeListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = Peritaje
    template_name = 'legal/peritaje_list.html'
    context_object_name = 'peritajes'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
        'demandante', 'demandado', 'abogado_responsable', 'perito_asignado', 'asunto', 'num_reparto',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'fecha': 'fecha_correo_electronico',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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
class PagoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = PagoSentenciaJudicial
    template_name = 'legal/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_pago', 'despacho_tramitante', 'medio_control',
        'demandante', 'demandado', 'abogado_responsable', 'valor_pagado', 'estado', 'tipo_pago',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'fecha': 'fecha_pago',
        'despacho': 'despacho_tramitante',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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
class SancionatorioListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = ProcesoAdministrativoSancionatorio
    template_name = 'legal/sancionatorio_list.html'
    context_object_name = 'procesos'
    paginate_by = 10
    search_fields = (
        'num_proceso', 'fecha_requerimiento', 'entidad', 'causa', 'estado',
        'entidad_solicitante_requerimiento', 'objeto_requerimiento',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_proceso': 'num_proceso',
        'fecha': 'fecha_requerimiento',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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
class RequerimientoListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = RequerimientoEnteControl
    template_name = 'legal/requerimiento_list.html'
    context_object_name = 'requerimientos'
    paginate_by = 10
    search_fields = (
        'num_reparto', 'num_proceso', 'fecha_correo_electronico',
        'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable', 'tipo_tramite',
    )
    sort_allowed_fields = {
        'id': 'id',
        'num_reparto': 'num_reparto',
        'num_proceso': 'num_proceso',
        'fecha': 'fecha_correo_electronico',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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
@require_http_methods(['DELETE', 'POST'])
def eliminar_registro(request, tipo, id_obj):
    # Log para depuración
    with open('error_log.txt', 'a') as f:
        f.write(f"\n[DELETE] Intento eliminar: tipo={tipo}, id={id_obj}, method={request.method}\n")
    
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
        try:
            obj = get_object_or_404(modelo, id=id_obj)
            obj.delete()
            with open('error_log.txt', 'a') as f:
                f.write(f"  -> Eliminado correctamente: {tipo} ID {id_obj}\n")
            return HttpResponse('') # HTMX vacía el TR
        except Exception as e:
            with open('error_log.txt', 'a') as f:
                f.write(f"  -> ERROR al eliminar: {str(e)}\n")
            return HttpResponse(f'Error: {str(e)}', status=500)
    
    return HttpResponse('Modelo no encontrado', status=400)

class ExtrajudicialListView(LoginRequiredMixin, RoleFilteringMixin, SearchMixin, SortMixin, ListView):
    model = ProcesoExtrajudicial
    template_name = 'legal/extrajudicial_list.html'
    context_object_name = 'extrajudiciales'
    paginate_by = 10
    search_fields = (
        'demandante', 'demandado', 'apoderado', 'medio_control', 'despacho_conocimiento', 'estado', 'clasificacion',
    )
    extrajudicial_filtro = 'todos'
    sort_allowed_fields = {
        'id': 'id',
        'despacho': 'despacho_conocimiento',
        'estado': 'estado',
    }
    sort_default_field = 'id'
    sort_default_dir = 'desc'

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

@require_GET
def buscar_tercero_nexus(request):
    """
    Consulta el nombre de un tercero en la base de datos de Nexus (GENTERCER) por su cédula.
    """
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'success': False, 'message': 'Cédula requerida'})
    
    try:
        with connections['readonly'].cursor() as cursor:
            # Según usuarios/views.py, los campos correctos en HUDN son:
            # Identificación: TERNUMDOC
            # Nombres: TERPRINOM, TERSEGNOM, TERPRIAPE, TERSEGAPE
            sql = """
                SELECT 
                    LTRIM(RTRIM(
                        ISNULL(TERPRINOM, '') + ' ' + 
                        ISNULL(TERSEGNOM, '') + ' ' + 
                        ISNULL(TERPRIAPE, '') + ' ' + 
                        ISNULL(TERSEGAPE, '')
                    )) 
                FROM GENTERCER 
                WHERE TERNUMDOC = %s
            """
            cursor.execute(sql, [cedula])
            row = cursor.fetchone()
            
            if row and row[0].strip():
                return JsonResponse({
                    'success': True,
                    'nombre': row[0].strip()
                })
            
            # Intento alternativo por si es un Usuario de Sistema (GENUSUARIO)
            cursor.execute("SELECT USUDESCRI FROM GENUSUARIO WHERE NumeroDocumento = %s", [cedula])
            row = cursor.fetchone()
            if row:
                return JsonResponse({
                    'success': True,
                    'nombre': row[0].strip()
                })

            return JsonResponse({'success': False, 'message': 'No encontrado en Nexus'})
    except Exception as e:
        logger.error(f"Error buscando tercero en Nexus: {e}")
        return JsonResponse({'success': False, 'message': 'Error de conexion con la base de datos'})


@require_GET
def cargar_despachos_judiciales(request):
    """
    Vista temporal de administracion: crea la tabla despachoJudicial y carga los datos del Excel.
    Solo accesible por superusuarios.
    """
    import os, openpyxl
    from django.db import connection as default_conn

    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Acceso denegado'}, status=403)

    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..', 'despachoJudicial.xlsx'
    )
    excel_path = os.path.normpath(excel_path)

    if not os.path.exists(excel_path):
        return JsonResponse({'success': False, 'message': f'Excel no encontrado en: {excel_path}'})

    try:
        # Leer Excel
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        rows = []
        for row_num in range(2, ws.max_row + 1):
            ciudad = ws.cell(row_num, 2).value
            nombre = ws.cell(row_num, 3).value
            correo = ws.cell(row_num, 4).value
            if nombre:
                rows.append((
                    str(ciudad).strip() if ciudad else '',
                    str(nombre).strip(),
                    str(correo).strip() if correo else None
                ))

        with default_conn.cursor() as cursor:
            # Crear tabla si no existe
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'defenjur_app_despachojudicial'
                )
                CREATE TABLE defenjur_app_despachojudicial (
                    id     INT IDENTITY(1,1) PRIMARY KEY,
                    ciudad NVARCHAR(100) NOT NULL,
                    nombre NVARCHAR(255) NOT NULL,
                    correo NVARCHAR(255) NULL
                )
            """)
            default_conn.commit()

            # TRUNCATE reinicia el contador de ID a 1
            cursor.execute("TRUNCATE TABLE defenjur_app_despachojudicial")
            for row in rows:
                cursor.execute(
                    "INSERT INTO defenjur_app_despachojudicial (ciudad, nombre, correo) VALUES (%s, %s, %s)",
                    list(row)
                )
            default_conn.commit()

            cursor.execute("SELECT COUNT(*) FROM defenjur_app_despachojudicial")
            total = cursor.fetchone()[0]

        return JsonResponse({
            'success': True,
            'message': f'Tabla creada y {total} despachos cargados correctamente.',
            'total': total
        })

    except Exception as e:
        logger.error(f"Error cargando despachos: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
def aplicar_migracion_auditoria(request):
    """Vista temporal: aplica ALTER TABLE para agregar columnas de auditoría a AccionTutela."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Acceso denegado'}, status=403)
    from django.db import connection
    resultados = []
    sqls = [
        ("fecha_registro", "ALTER TABLE defenjur_app_acciontutela ADD fecha_registro DATETIME2 NULL"),
        ("usuario_carga",  "ALTER TABLE defenjur_app_acciontutela ADD usuario_carga NVARCHAR(150) NULL"),
    ]
    try:
        with connection.cursor() as cursor:
            for col, sql in sqls:
                cursor.execute(f"""
                    IF NOT EXISTS (
                        SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME='defenjur_app_acciontutela' AND COLUMN_NAME='{col}'
                    ) EXEC('{sql}')
                """)
                resultados.append(f"Columna '{col}': OK")
            connection.commit()
        return JsonResponse({'success': True, 'resultados': resultados})
    except Exception as e:
        logger.error(f"Error aplicando migración auditoría: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


# ─── CRUD Despachos Judiciales ────────────────────────────────────────────────

class DespachoJudicialListView(LoginRequiredMixin, ListView):
    model = DespachoJudicial
    template_name = 'legal/despacho_list.html'
    context_object_name = 'despachos'
    paginate_by = 20

    def get_queryset(self):
        try:
            qs = DespachoJudicial.objects.all()
            q = self.request.GET.get('q', '').strip()
            if q:
                qs = qs.filter(Q(nombre__icontains=q) | Q(ciudad__icontains=q))
            return qs
        except Exception:
            return DespachoJudicial.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        try:
            ctx['total'] = DespachoJudicial.objects.count()
        except Exception:
            ctx['total'] = 0
            ctx['tabla_pendiente'] = True
        return ctx


class DespachoJudicialCreateView(LoginRequiredMixin, CreateView):
    model = DespachoJudicial
    fields = ['ciudad', 'nombre', 'correo']
    template_name = 'legal/despacho_form.html'
    success_url = reverse_lazy('despachos_lista')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'premium-input'
            field.widget.attrs.setdefault('placeholder', field.label)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Despacho judicial registrado correctamente.')
        return super().form_valid(form)


class DespachoJudicialUpdateView(LoginRequiredMixin, UpdateView):
    model = DespachoJudicial
    fields = ['ciudad', 'nombre', 'correo']
    template_name = 'legal/despacho_form.html'
    success_url = reverse_lazy('despachos_lista')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'premium-input'
            field.widget.attrs.setdefault('placeholder', field.label)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Despacho judicial actualizado correctamente.')
        return super().form_valid(form)


@login_required
@require_POST
def despacho_eliminar(request, pk):
    if not _is_app_admin(request.user):
        raise PermissionDenied
    obj = get_object_or_404(DespachoJudicial, pk=pk)
    obj.delete()
    messages.success(request, 'Despacho eliminado correctamente.')
    return redirect('despachos_lista')


