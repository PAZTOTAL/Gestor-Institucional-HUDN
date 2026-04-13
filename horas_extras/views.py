from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from .models import HoraExtra
from django.apps import apps
from django.db.models import Q
from django.utils import timezone

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
