import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import (HoraExtra, AreaRecargos, TrabajadorRecargos, TurnoRecargos,
                     ObservacionMensualRecargos, PerfilRecargos)
from .utils.holidays import festivos_colombia, festivos_mes
from .utils.report import (generar_planilla, generar_planilla_area,
                            EmpleadoInfo, MESES_ES, calcular_horas,
                            DIAS_ES, TURNOS_LABEL)
from django.apps import apps

class TalentoHumanoDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/talento_humano_dashboard.html'

class HoraExtraListView(LoginRequiredMixin, ListView):
    model = HoraExtra
    template_name = 'horas_extras/hora_extra_list.html'
    context_object_name = 'registros'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CargarHorasView(LoginRequiredMixin, CreateView):
    model = HoraExtra
    template_name = 'horas_extras/cargar.html'
    fields = [
        'empleado_oid', 'nombre_empleado', 'documento_empleado', 'fecha',
        'horas_recargo_nocturno', 'horas_recargo_dominical_diurno', 'horas_recargo_dominical_nocturno',
        'horas_extra_diurna', 'horas_extra_nocturna', 'horas_extra_dominical_diurna', 'horas_extra_dominical_nocturna',
        'observaciones'
    ]
    success_url = reverse_lazy('horas_extras:hora_extra_list')

    def form_valid(self, form):
        form.instance.usuario_registro = self.request.user
        messages.success(self.request, "Horas extras cargadas exitosamente.")
        return super().form_valid(form)

def buscar_empleado(request):
    term = request.GET.get('term', '')
    if not term:
        return JsonResponse({'results': []})
    
    try:
        Nmemplea = apps.get_model('consultas_externas', 'Nmemplea')
        # Buscamos en Nmemplea los empleados activos
        # nemcodigo es el documento/codigo, nemnomcom es el nombre completo
        results = Nmemplea.objects.using('readonly').filter(
            Q(nemcodigo__icontains=term) | 
            Q(nemnomcom__icontains=term)
        ).filter(nemestado=1)[:15]
        
        data = []
        for r in results:
            data.append({
                'id': r.nemcodigo, # Usamos nemcodigo como ID
                'documento': r.nemcodigo,
                'nombre': r.nemnomcom.strip(),
                'text': f"{r.nemcodigo} - {r.nemnomcom.strip()}"
            })
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'error': str(e), 'results': []})

class InformesDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/informes_dashboard.html'

class PersonalActivoReportView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_personal_activo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db import connections
        
        with connections['readonly'].cursor() as cursor:
            # Personal Permanente: NEMTIPCON = 1 AND NEMCLAEMP = 3 (Validado por el usuario)
            cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 3")
            context['total_activo'] = cursor.fetchone()[0]
            
            # Distribución por vinculación (solo para permanentes)
            cursor.execute("""
                SELECT v.VINNOMBRE, COUNT(*) 
                FROM NMEMPLEA e
                JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 3
                GROUP BY v.VINNOMBRE
            """)
            context['vinculaciones'] = cursor.fetchall()

        context['total_activos'] = context['total_activo']
        context['fecha_corte'] = timezone.now()
        return context

class PersonalPorAreaReportView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_personal_area.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db import connections
        
        with connections['readonly'].cursor() as cursor:
            # Distribución de Personal PERMANENTE por Area
            query = """
                SELECT 
                    ISNULL(c.CCCODIGO, 'SIN-AREA') as area_code,
                    ISNULL(c.CCNOMBRE, 'SIN AREA ASIGNADA') as area_name,
                    COUNT(e.NEMCODIGO) as total
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 3
                GROUP BY c.CCCODIGO, c.CCNOMBRE
                ORDER BY COUNT(e.NEMCODIGO) DESC
            """
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            areas = [dict(zip(columns, row)) for row in cursor.fetchall()]

        context['areas'] = areas
        context['total_empleados'] = sum(a['total'] for a in areas)
        context['fecha_corte'] = timezone.now()
        return context

class PersonalAreaDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_personal_area_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        area_code = self.kwargs.get('area_code')
        from django.db import connections
        
        with connections['readonly'].cursor() as cursor:
            # Preparar parámetros y filtro
            if area_code == 'SIN-AREA':
                context['area_name'] = 'SIN AREA ASIGNADA'
                # Incluimos: NULL, vacíos, o códigos que no existen en la tabla maestra CTNCENCOS
                filter_sql = """
                    WHERE e.NEMESTADO = 1 AND (
                        e.GASCODIGO IS NULL OR 
                        RTRIM(LTRIM(e.GASCODIGO)) = '' OR 
                        NOT EXISTS (SELECT 1 FROM CTNCENCOS c2 WHERE RTRIM(LTRIM(c2.CCCODIGO)) = RTRIM(LTRIM(e.GASCODIGO)))
                    )
                """
                params = []
            else:
                cursor.execute("SELECT CCNOMBRE FROM CTNCENCOS WHERE RTRIM(LTRIM(CCCODIGO)) = %s", [area_code.strip()])
                res = cursor.fetchone()
                context['area_name'] = res[0] if res else 'Área Desconocida'
                filter_sql = "WHERE e.NEMESTADO = 1 AND RTRIM(LTRIM(e.GASCODIGO)) = %s"
                params = [area_code.strip()]

            # Obtener lista de funcionarios
            filtro_tipo = self.request.GET.get('filtro', '')
            # Si es temporal filtramos por clase 0, si no (por defecto) es permanente clase 3
            clase_sql = " AND e.NEMCLAEMP = 0" if filtro_tipo == 'temporal' else " AND e.NEMCLAEMP = 3"
            
            # Reemplazar NEMESTADO=1 por NEMESTADO=1 + clase_sql
            current_filter = filter_sql.replace("WHERE e.NEMESTADO = 1", f"WHERE e.NEMESTADO = 1{clase_sql}")

            query = f"""
                SELECT 
                    e.NEMCODIGO as documento,
                    e.NEMNOMCOM as nombre,
                    e.NEMFECING as fecha_ingreso,
                    v.VINNOMBRE as vinculacion
                FROM NMEMPLEA e
                LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                {current_filter}
                ORDER BY e.NEMNOMCOM ASC
            """
            cursor.execute(query, params)
                
            columns = [col[0] for col in cursor.description]
            funcionarios = [dict(zip(columns, row)) for row in cursor.fetchall()]

        context['funcionarios'] = funcionarios
        context['area_code'] = area_code
        context['filtro'] = self.request.GET.get('filtro', '')
        return context

class PersonalTemporalReportView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_personal_temporal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db import connections
        
        with connections['readonly'].cursor() as cursor:
            # 1. Totales
            cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1")
            context['total_activos'] = cursor.fetchone()[0]
            
            # Ajuste según feedback: NEMCLAEMP = 0 como Temporal (158 registros)
            cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 0")
            context['total_temporal'] = cursor.fetchone()[0]

            # 2. Distribución por áreas (solo temporales - Clase 0)
            query = """
                SELECT 
                    ISNULL(c.CCCODIGO, 'SIN-AREA') as area_code,
                    ISNULL(c.CCNOMBRE, 'SIN AREA ASIGNADA') as area_name,
                    COUNT(e.NEMCODIGO) as total
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 0
                GROUP BY c.CCCODIGO, c.CCNOMBRE
                ORDER BY COUNT(e.NEMCODIGO) DESC
            """
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            context['areas_temporal'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

        context['fecha_corte'] = timezone.now()
        return context

class BuscarFuncionarioView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/buscar_funcionario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        context['query'] = q
        
        if q:
            from django.db import connections
            with connections['readonly'].cursor() as cursor:
                # 1. Intentar en NMEMPLEA (Novedades/Nómina Principal)
                query_primary = """
                    SELECT 
                        e.NEMCODIGO as documento,
                        e.NEMNOMCOM as nombre,
                        e.NEMFECING as fecha_ingreso,
                        ISNULL(c.CCNOMBRE, 'SIN AREA ASIGNADA') as area,
                        v.VINNOMBRE as vinculacion,
                        cr.NCENOMBRE as cargo,
                        CASE WHEN e.NEMCLAEMP = 3 THEN 'PLANTA PERMANENTE' ELSE 'PLANTA TEMPORAL' END as tipo_planta,
                        CASE WHEN e.NEMESTADO = 1 THEN 'ACTIVO' ELSE 'INACTIVO' END as estado
                    FROM NMEMPLEA e
                    LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                    LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                    LEFT JOIN NMCARGOS cr ON RTRIM(LTRIM(e.NCECODIGO)) = RTRIM(LTRIM(cr.NCECODIGO))
                    WHERE e.NEMCODIGO = %s OR RTRIM(LTRIM(e.NEMCODIGO)) = %s
                """
                cursor.execute(query_primary, [q, q])
                columns = [col[0] for col in cursor.description]
                res = cursor.fetchone()
                
                if res:
                    context['funcionario'] = dict(zip(columns, res))
                    context['fuente'] = 'NMEMPLEA'
                else:
                    # 2. Fallback a NOMEMPLEADO (Superset de empleados)
                    query_fallback = """
                        SELECT 
                            e.EMPCODIGO as documento,
                            (ISNULL(e.EMPNOMBRE1, '') + ' ' + ISNULL(e.EMPNOMBRE2, '') + ' ' + 
                             ISNULL(e.EMPAPELLI1, '') + ' ' + ISNULL(e.EMPAPELLI2, '') ) as nombre,
                            i.ILFECINGRE as fecha_ingreso,
                            ISNULL(s.SUBNOMBRE, 'AREA NO ESPECIFICADA') as area,
                            'PLANTA' as vinculacion,
                            'CARGO ADMINISTRATIVO' as cargo,
                            'PLANTA PERMANENTE' as tipo_planta,
                            'ACTIVO' as estado
                        FROM NOMEMPLEADO e
                        LEFT JOIN NOMINFOLAB i ON e.NOMINFOLAB = i.OID
                        LEFT JOIN NOMSUBGRU s ON e.NOMSUBGRU = s.OID
                        WHERE e.EMPCODIGO = %s OR RTRIM(LTRIM(e.EMPCODIGO)) = %s
                    """
                    cursor.execute(query_fallback, [q, q])
                    if cursor.description:
                        columns_f = [col[0] for col in cursor.description]
                        res_f = cursor.fetchone()
                        if res_f:
                            context['funcionario'] = dict(zip(columns_f, res_f))
                            context['fuente'] = 'NOMEMPLEADO'
                        else:
                            context['error'] = "No se encontró ningún funcionario con ese número de documento en ninguna nómina."
                    else:
                        context['error'] = "Error al consultar la base de datos de empleados."

        return context


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO RECARGOS / TURNOS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_perfil_recargos(user):
    """Obtiene o crea el perfil de recargos. Superuser → admin."""
    try:
        return user.perfil_recargos
    except PerfilRecargos.DoesNotExist:
        if user.is_superuser:
            return PerfilRecargos.objects.create(user=user, rol='admin')
        return None


def _es_admin_recargos(user):
    p = _get_perfil_recargos(user)
    return p is not None and p.es_admin()


def _areas_ids_recargos(user):
    """None = todas, lista = áreas del coordinador."""
    p = _get_perfil_recargos(user)
    if p is None or p.es_admin():
        return None
    return list(p.areas.values_list('id', flat=True))


# ── Vistas de plantilla ───────────────────────────────────────────────────────

class TurnosRecargosView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/turnos_recargos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['es_admin'] = _es_admin_recargos(self.request.user)
        return ctx


class ConfiguracionRecargosView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/configuracion_recargos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['es_admin'] = _es_admin_recargos(self.request.user)
        return ctx


class ReporteRecargosView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_recargos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['es_admin'] = _es_admin_recargos(self.request.user)
        return ctx


# ── API: Áreas ────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def api_areas(request):
    ids = _areas_ids_recargos(request.user)

    if request.method == 'GET':
        qs = AreaRecargos.objects.annotate(total_trabajadores=Count('trabajadores'))
        if ids is not None:
            qs = qs.filter(id__in=ids)
        data = [{'id': a.id, 'nombre': a.nombre, 'descripcion': a.descripcion,
                 'total_trabajadores': a.total_trabajadores} for a in qs]
        return JsonResponse(data, safe=False)

    if not _es_admin_recargos(request.user):
        return JsonResponse({'error': 'Solo el administrador puede crear áreas'}, status=403)
    body = json.loads(request.body)
    nombre = body.get('nombre', '').strip()
    if not nombre:
        return JsonResponse({'error': 'El nombre es obligatorio'}, status=400)
    area = AreaRecargos.objects.create(nombre=nombre, descripcion=body.get('descripcion', ''))
    return JsonResponse({'id': area.id, 'nombre': area.nombre,
                         'descripcion': area.descripcion, 'total_trabajadores': 0}, status=201)


@login_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def api_area_detail(request, pk):
    area = get_object_or_404(AreaRecargos, pk=pk)
    if request.method == 'GET':
        return JsonResponse({'id': area.id, 'nombre': area.nombre, 'descripcion': area.descripcion})
    if not _es_admin_recargos(request.user):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    if request.method == 'DELETE':
        area.delete()
        return JsonResponse({'ok': True})
    body = json.loads(request.body)
    area.nombre      = body.get('nombre', area.nombre).strip()
    area.descripcion = body.get('descripcion', area.descripcion)
    area.save()
    return JsonResponse({'id': area.id, 'nombre': area.nombre, 'descripcion': area.descripcion})


# ── API: Empleados ────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def api_empleados(request):
    ids = _areas_ids_recargos(request.user)
    area_id = request.GET.get('area')

    if request.method == 'GET':
        qs = TrabajadorRecargos.objects.select_related('area').all()
        if area_id:
            qs = qs.filter(area_id=area_id)
        if ids is not None:
            qs = qs.filter(area_id__in=ids)
        data = [{'id': t.id, 'nombre': t.nombre, 'documento': t.documento,
                 'cargo': t.cargo, 'area': t.area_id, 'area_nombre': t.area.nombre,
                 'tipo': t.tipo, 'tipo_display': t.get_tipo_display()} for t in qs]
        return JsonResponse(data, safe=False)

    body = json.loads(request.body)
    a_id = body.get('area')
    if ids is not None and int(a_id) not in ids:
        return JsonResponse({'error': 'Sin acceso a esa área'}, status=403)
    try:
        area = AreaRecargos.objects.get(pk=a_id)
    except AreaRecargos.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)
    t = TrabajadorRecargos.objects.create(
        nombre=body.get('nombre', '').strip(),
        documento=body.get('documento', '').strip(),
        cargo=body.get('cargo', '').strip(),
        area=area,
        tipo=body.get('tipo', 'permanente'),
    )
    return JsonResponse({'id': t.id, 'nombre': t.nombre, 'documento': t.documento,
                         'cargo': t.cargo, 'area': t.area_id, 'area_nombre': t.area.nombre,
                         'tipo': t.tipo, 'tipo_display': t.get_tipo_display()}, status=201)


@login_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def api_empleado_detail(request, pk):
    t = get_object_or_404(TrabajadorRecargos, pk=pk)
    ids = _areas_ids_recargos(request.user)
    if ids is not None and t.area_id not in ids:
        return JsonResponse({'error': 'Sin acceso'}, status=403)
    if request.method == 'GET':
        return JsonResponse({'id': t.id, 'nombre': t.nombre, 'documento': t.documento,
                             'cargo': t.cargo, 'area': t.area_id, 'tipo': t.tipo})
    if request.method == 'DELETE':
        t.delete()
        return JsonResponse({'ok': True})
    body = json.loads(request.body)
    if 'nombre'    in body: t.nombre    = body['nombre'].strip()
    if 'documento' in body: t.documento = body['documento'].strip()
    if 'cargo'     in body: t.cargo     = body['cargo'].strip()
    if 'tipo'      in body: t.tipo      = body['tipo']
    if 'area'      in body:
        a_id = int(body['area'])
        if ids is not None and a_id not in ids:
            return JsonResponse({'error': 'Sin acceso a esa área'}, status=403)
        t.area_id = a_id
    t.save()
    t.refresh_from_db()
    return JsonResponse({'id': t.id, 'nombre': t.nombre, 'documento': t.documento,
                         'cargo': t.cargo, 'area': t.area_id, 'area_nombre': t.area.nombre,
                         'tipo': t.tipo, 'tipo_display': t.get_tipo_display()})


# ── API: Turnos ───────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def api_turnos(request):
    if request.method == 'GET':
        emp_id = request.GET.get('empleado_id')
        year   = request.GET.get('year')
        month  = request.GET.get('month')
        qs = TurnoRecargos.objects.all()
        if emp_id:  qs = qs.filter(empleado_id=emp_id)
        if year:    qs = qs.filter(fecha__year=year)
        if month:   qs = qs.filter(fecha__month=month)
        data = [{'id': t.id, 'empleado_id': t.empleado_id, 'fecha': str(t.fecha),
                 'turno': t.turno, 'observaciones': t.observaciones,
                 'horas_diurnas': t.horas_diurnas, 'horas_nocturnas': t.horas_nocturnas}
                for t in qs]
        return JsonResponse(data, safe=False)

    body = json.loads(request.body)
    emp_id = body.get('empleado_id')
    fecha  = body.get('fecha')
    turno  = body.get('turno')
    existing = TurnoRecargos.objects.filter(empleado_id=emp_id, fecha=fecha).first()
    if existing:
        existing.turno           = turno
        existing.observaciones   = body.get('observaciones', existing.observaciones)
        existing.horas_diurnas   = body.get('horas_diurnas')
        existing.horas_nocturnas = body.get('horas_nocturnas')
        existing.save()
        t = existing
    else:
        t = TurnoRecargos.objects.create(
            empleado_id=emp_id, fecha=fecha, turno=turno,
            observaciones=body.get('observaciones', ''),
            horas_diurnas=body.get('horas_diurnas'),
            horas_nocturnas=body.get('horas_nocturnas'),
        )
    return JsonResponse({'id': t.id, 'empleado_id': t.empleado_id, 'fecha': str(t.fecha),
                         'turno': t.turno, 'horas_diurnas': t.horas_diurnas,
                         'horas_nocturnas': t.horas_nocturnas}, status=200)


@login_required
@require_http_methods(['DELETE'])
def api_turno_detail(request, pk):
    t = get_object_or_404(TurnoRecargos, pk=pk)
    t.delete()
    return JsonResponse({'ok': True})


# ── API: Festivos ─────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def api_festivos(request):
    year  = request.GET.get('year')
    month = request.GET.get('month')
    if not year:
        return JsonResponse({'error': 'Se requiere year'}, status=400)
    year = int(year)
    result = festivos_mes(year, int(month)) if month else festivos_colombia(year)
    return JsonResponse(result)


# ── API: Observación mensual ──────────────────────────────────────────────────

@login_required
def api_observacion_mensual(request):
    if request.method == 'GET':
        emp_id = request.GET.get('empleado_id')
        year   = request.GET.get('year')
        month  = request.GET.get('month')
        obj = ObservacionMensualRecargos.objects.filter(
            empleado_id=emp_id, year=year, month=month).first()
        return JsonResponse({'observacion': obj.observacion if obj else ''})

    body   = json.loads(request.body)
    emp_id = body.get('empleado_id')
    year   = body.get('year')
    month  = body.get('month')
    obs, _ = ObservacionMensualRecargos.objects.get_or_create(
        empleado_id=emp_id, year=year, month=month)
    obs.observacion = body.get('observacion', '')
    obs.save()
    return JsonResponse({'ok': True})


# ── API: Reportes Excel ───────────────────────────────────────────────────────

@login_required
def api_reporte_xlsx(request):
    emp_id = request.GET.get('empleado_id')
    year   = int(request.GET.get('year',  0))
    month  = int(request.GET.get('month', 0))
    if not all([emp_id, year, month]):
        return JsonResponse({'error': 'Se requieren empleado_id, year y month'}, status=400)

    try:
        t = TrabajadorRecargos.objects.select_related('area').get(pk=emp_id)
        emp = EmpleadoInfo(id=t.id, nombre=t.nombre, documento=t.documento,
                           cargo=t.cargo, area_nombre=t.area.nombre, tipo=t.tipo)
    except TrabajadorRecargos.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)

    turnos_qs   = TurnoRecargos.objects.filter(empleado_id=emp_id, fecha__year=year, fecha__month=month)
    turnos_dict = {str(tr.fecha): (tr.turno, tr.horas_diurnas or 0, tr.horas_nocturnas or 0) for tr in turnos_qs}
    xlsx = generar_planilla(emp, year, month, turnos_dict)
    filename = f"Planilla_{emp.nombre.replace(' ','_')}_{MESES_ES[month]}_{year}.xlsx"
    resp = HttpResponse(xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


@login_required
def api_reporte_area_xlsx(request):
    area_id = request.GET.get('area')
    year    = int(request.GET.get('year',  0))
    month   = int(request.GET.get('month', 0))
    if not all([area_id, year, month]):
        return JsonResponse({'error': 'Se requieren area, year y month'}, status=400)

    try:
        area = AreaRecargos.objects.get(pk=area_id)
    except AreaRecargos.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)

    ids = _areas_ids_recargos(request.user)
    if ids is not None and int(area_id) not in ids:
        return JsonResponse({'error': 'Sin acceso a esta área'}, status=403)

    trabajadores = TrabajadorRecargos.objects.filter(area=area).select_related('area')
    coord_nombre = request.user.get_full_name() or request.user.username
    empleados_turnos = []
    for t in sorted(trabajadores, key=lambda x: (x.tipo, x.nombre)):
        emp    = EmpleadoInfo(id=t.id, nombre=t.nombre, documento=t.documento,
                              cargo=t.cargo, area_nombre=area.nombre, tipo=t.tipo)
        turnos = TurnoRecargos.objects.filter(empleado_id=t.id, fecha__year=year, fecha__month=month)
        empleados_turnos.append((emp, {str(tr.fecha): (tr.turno, tr.horas_diurnas or 0, tr.horas_nocturnas or 0) for tr in turnos}))

    xlsx = generar_planilla_area(area, year, month, empleados_turnos, coordinador_nombre=coord_nombre)
    filename = f"Planilla_{area.nombre.replace(' ','_')}_{MESES_ES[month]}_{year}.xlsx"
    resp = HttpResponse(xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


# ── API: Coordinadores ────────────────────────────────────────────────────────

@login_required
@require_http_methods(['GET', 'POST'])
def api_coordinadores(request):
    if not _es_admin_recargos(request.user):
        return JsonResponse({'error': 'Solo el administrador puede gestionar coordinadores'}, status=403)

    if request.method == 'GET':
        items = PerfilRecargos.objects.filter(rol='coordinador').select_related('user').prefetch_related('areas')
        data  = [{'id': p.id, 'username': p.user.username,
                  'nombre': p.user.get_full_name() or p.user.username,
                  'first_name': p.user.first_name, 'last_name': p.user.last_name,
                  'documento': p.documento,
                  'areas': [{'id': a.id, 'nombre': a.nombre} for a in p.areas.all()]}
                 for p in items]
        return JsonResponse(data, safe=False)

    body     = json.loads(request.body)
    username = body.get('username', '').strip()
    password = body.get('password', '')
    if not username or not password:
        return JsonResponse({'error': 'Usuario y contraseña son obligatorios'}, status=400)
    if len(password) < 6:
        return JsonResponse({'error': 'La contraseña debe tener al menos 6 caracteres'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'El nombre de usuario ya existe'}, status=400)
    user = User.objects.create_user(username=username, password=password,
                                    first_name=body.get('first_name', ''),
                                    last_name=body.get('last_name', ''))
    p = PerfilRecargos.objects.create(user=user, rol='coordinador',
                                      documento=body.get('documento', ''))
    if body.get('areas'):
        p.areas.set(AreaRecargos.objects.filter(id__in=body['areas']))
    return JsonResponse({'id': p.id, 'username': user.username,
                         'nombre': user.get_full_name() or user.username,
                         'documento': p.documento,
                         'areas': [{'id': a.id, 'nombre': a.nombre} for a in p.areas.all()]}, status=201)


@login_required
@require_http_methods(['GET'])
def api_reporte_pdf(request):
    """Genera el PDF institucional FRRHU-030 para un área/mes/tipo."""
    import calendar as _cal
    from datetime import date as _date, timedelta as _td
    from .utils.html_pdf import generar_pdf_html

    area_id = request.GET.get('area')
    year    = request.GET.get('year')
    month   = request.GET.get('month')
    tipo    = request.GET.get('tipo')          # 'temporal' | 'permanente' | None

    if not all([area_id, year, month]):
        return JsonResponse({'error': 'Se requieren area, year y month'}, status=400)

    ids = _areas_ids_recargos(request.user)
    if ids is not None and int(area_id) not in ids:
        return JsonResponse({'error': 'Sin acceso a esta área'}, status=403)

    try:
        area = AreaRecargos.objects.get(pk=area_id)
    except AreaRecargos.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)

    year, month = int(year), int(month)
    festivos_dict = festivos_colombia(year)

    trabajadores = TrabajadorRecargos.objects.filter(area=area)
    if tipo in ('temporal', 'permanente'):
        trabajadores = trabajadores.filter(tipo=tipo)

    obs_map = {
        o.empleado_id: o.observacion
        for o in ObservacionMensualRecargos.objects.filter(
            empleado_id__in=list(trabajadores.values_list('id', flat=True)),
            year=year, month=month
        )
    }

    from datetime import date as _date2, timedelta as _td2
    empleados_data = []
    for t in sorted(trabajadores, key=lambda x: (x.tipo, x.nombre)):
        turnos_qs = TurnoRecargos.objects.filter(empleado_id=t.id, fecha__year=year, fecha__month=month)
        hon = hdf = hnf = 0
        for tr in turnos_qs:
            fstr   = str(tr.fecha)
            fecha  = _date2.fromisoformat(fstr)
            esp    = fecha.weekday() == 6 or fstr in festivos_dict
            sig    = fecha + _td2(days=1)
            sig_esp = sig.weekday() == 6 or str(sig) in festivos_dict
            h = calcular_horas(tr.turno, esp, tr.horas_diurnas or 0, tr.horas_nocturnas or 0, sig_esp)
            hon += h[1]; hdf += h[2]; hnf += h[3]
        empleados_data.append({
            'documento':     t.documento,
            'nombre':        t.nombre,
            'tipo':          t.tipo,
            'hon':           hon,
            'hdf':           hdf,
            'hnf':           hnf,
            'observaciones': obs_map.get(t.id, ''),
        })

    coord_nombre = request.user.get_full_name() or request.user.username
    try:
        pdf_bytes = generar_pdf_html(area.nombre, year, month, empleados_data,
                                     tipo=tipo, coordinador_nombre=coord_nombre)
    except Exception as e:
        return JsonResponse({'error': f'Error al generar PDF: {e}'}, status=500)

    tipo_sufijo = f'_{tipo.capitalize()}' if tipo in ('temporal', 'permanente') else ''
    filename = f"FRRHU-030_{area.nombre.replace(' ','_')}_{MESES_ES[month]}_{year}{tipo_sufijo}.pdf"
    resp = HttpResponse(pdf_bytes, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


@login_required
@require_http_methods(['GET'])
def api_preview_area(request):
    """Retorna resumen de recargos HON/HDF/HNF para todos los empleados del área en el mes."""
    import calendar as _cal
    from datetime import date as _date, timedelta as _td

    area_id = request.GET.get('area')
    year    = request.GET.get('year')
    month   = request.GET.get('month')
    if not all([area_id, year, month]):
        return JsonResponse({'error': 'Se requieren area, year y month'}, status=400)

    ids = _areas_ids_recargos(request.user)
    if ids is not None and int(area_id) not in ids:
        return JsonResponse({'error': 'Sin acceso a esta área'}, status=403)

    try:
        area = AreaRecargos.objects.get(pk=area_id)
    except AreaRecargos.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)

    year, month = int(year), int(month)
    festivos    = festivos_colombia(year)
    num_dias    = _cal.monthrange(year, month)[1]
    trabajadores = TrabajadorRecargos.objects.filter(area=area).select_related('area')

    resultado  = []
    tot_global = {'hon': 0, 'hdf': 0, 'hnf': 0}

    for t in sorted(trabajadores, key=lambda x: (x.tipo, x.nombre)):
        turnos_qs   = TurnoRecargos.objects.filter(empleado_id=t.id, fecha__year=year, fecha__month=month)
        turnos_dict = {str(tr.fecha): tr for tr in turnos_qs}

        hon = hdf = hnf = 0
        detalle = []

        for dia in range(1, num_dias + 1):
            fecha  = _date(year, month, dia)
            fstr   = str(fecha)
            es_dom = fecha.weekday() == 6
            es_fest = fstr in festivos
            especial = es_dom or es_fest
            tr_obj  = turnos_dict.get(fstr)

            if tr_obj:
                sig = fecha + _td(days=1)
                sig_esp = sig.weekday() == 6 or str(sig) in festivos
                hd = tr_obj.horas_diurnas  or 0
                hn = tr_obj.horas_nocturnas or 0
                hod_, hon_, hdf_, hnf_ = calcular_horas(tr_obj.turno, especial, hd, hn, sig_esp)
                hon += hon_; hdf += hdf_; hnf += hnf_
                tipo_dia = (f"Festivo ({festivos[fstr]})" if es_fest
                            else 'Domingo' if es_dom else 'Ordinario')
                detalle.append({
                    'dia': dia, 'fecha': fstr,
                    'dia_semana': DIAS_ES[fecha.weekday()],
                    'tipo_dia': tipo_dia,
                    'turno': TURNOS_LABEL.get(tr_obj.turno, tr_obj.turno),
                    'hod': hod_, 'hon': hon_, 'hdf': hdf_, 'hnf': hnf_,
                })

        tot_global['hon'] += hon
        tot_global['hdf'] += hdf
        tot_global['hnf'] += hnf

        resultado.append({
            'id': t.id, 'nombre': t.nombre, 'documento': t.documento,
            'cargo': t.cargo, 'tipo': t.tipo,
            'tipo_display': t.get_tipo_display(),
            'total_dias': len(turnos_dict),
            'hon': hon, 'hdf': hdf, 'hnf': hnf,
            'detalle': detalle,
        })

    return JsonResponse({
        'area': area.nombre,
        'mes': f'{MESES_ES[month]} {year}',
        'empleados': resultado,
        'totales': tot_global,
    })


@login_required
@require_http_methods(['PUT', 'DELETE'])
def api_coordinador_detail(request, pk):
    if not _es_admin_recargos(request.user):
        return JsonResponse({'error': 'Solo el administrador puede gestionar coordinadores'}, status=403)
    p = get_object_or_404(PerfilRecargos, pk=pk, rol='coordinador')
    if request.method == 'DELETE':
        p.user.delete()
        return JsonResponse({'ok': True})
    body = json.loads(request.body)
    user = p.user
    if 'first_name' in body: user.first_name = body['first_name']
    if 'last_name'  in body: user.last_name  = body['last_name']
    if body.get('password'):
        if len(body['password']) < 6:
            return JsonResponse({'error': 'La contraseña debe tener al menos 6 caracteres'}, status=400)
        user.set_password(body['password'])
    user.save()
    if 'documento' in body:
        p.documento = body['documento']
        p.save()
    if 'areas' in body:
        p.areas.set(AreaRecargos.objects.filter(id__in=body['areas']))
    return JsonResponse({'id': p.id, 'username': user.username,
                         'nombre': user.get_full_name() or user.username,
                         'documento': p.documento,
                         'areas': [{'id': a.id, 'nombre': a.nombre} for a in p.areas.all()]})


# ── API: Importar desde Nómina (DGEMPRES01) ───────────────────────────────────

@login_required
@require_http_methods(['GET'])
def api_nomina_dependencias(request):
    """Lista de dependencias activas en DGEMPRES01 que tienen al menos un empleado activo."""
    from django.db import connections
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("""
                SELECT RTRIM(LTRIM(c.CCCODIGO)) AS codigo,
                       RTRIM(LTRIM(c.CCNOMBRE)) AS nombre
                FROM   CTNCENCOS c
                WHERE  EXISTS (
                    SELECT 1 FROM NMEMPLEA e
                    WHERE  RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                    AND    e.NEMESTADO = 1
                )
                ORDER BY c.CCNOMBRE ASC
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return JsonResponse(rows, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=503)


@login_required
@require_http_methods(['GET'])
def api_nomina_empleados(request):
    """Empleados activos de una dependencia en DGEMPRES01."""
    dep = request.GET.get('dependencia', '').strip()
    if not dep:
        return JsonResponse({'error': 'dependencia requerida'}, status=400)
    from django.db import connections
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("""
                SELECT RTRIM(LTRIM(e.NEMCODIGO))  AS documento,
                       RTRIM(LTRIM(e.NEMNOMCOM))  AS nombre,
                       ISNULL(RTRIM(LTRIM(cr.NCENOMBRE)), '') AS cargo,
                       CASE WHEN e.NEMCLAEMP = 3 THEN 'permanente'
                            WHEN e.NEMCLAEMP = 0 THEN 'temporal'
                            ELSE 'ops' END        AS tipo
                FROM   NMEMPLEA e
                LEFT JOIN NMCARGOS cr
                       ON RTRIM(LTRIM(e.NCECODIGO)) = RTRIM(LTRIM(cr.NCECODIGO))
                WHERE  e.NEMESTADO = 1
                AND    RTRIM(LTRIM(e.GASCODIGO)) = %s
                ORDER BY e.NEMNOMCOM ASC
            """, [dep])
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        # Marcar cuáles ya existen en TrabajadorRecargos
        documentos_existentes = set(
            TrabajadorRecargos.objects.filter(
                documento__in=[r['documento'] for r in rows]
            ).values_list('documento', flat=True)
        )
        for r in rows:
            r['ya_existe'] = r['documento'] in documentos_existentes
        return JsonResponse(rows, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=503)


@login_required
@require_http_methods(['POST'])
def api_importar_empleados(request):
    """Importa empleados seleccionados de nómina a TrabajadorRecargos."""
    if not _es_admin_recargos(request.user):
        return JsonResponse({'error': 'Solo el administrador puede importar'}, status=403)
    body     = json.loads(request.body)
    area_id  = body.get('area')
    empleados = body.get('empleados', [])
    if not area_id or not empleados:
        return JsonResponse({'error': 'area y empleados son requeridos'}, status=400)
    area = get_object_or_404(AreaRecargos, pk=area_id)
    creados = omitidos = 0
    for emp in empleados:
        doc    = (emp.get('documento') or '').strip()
        nombre = (emp.get('nombre')    or '').strip()
        cargo  = (emp.get('cargo')     or '').strip()
        tipo   = emp.get('tipo', 'permanente')
        if tipo not in ('permanente', 'temporal', 'ops'):
            tipo = 'permanente'
        if not doc or not nombre:
            continue
        _, created = TrabajadorRecargos.objects.get_or_create(
            documento=doc,
            defaults={'nombre': nombre, 'cargo': cargo, 'area': area, 'tipo': tipo},
        )
        if created:
            creados += 1
        else:
            omitidos += 1
    return JsonResponse({'creados': creados, 'omitidos': omitidos})
