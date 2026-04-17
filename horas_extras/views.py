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
import pandas as pd
import os
from django.core.cache import cache

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
            # Personal Permanente: Class 0 (Older entries, verified by entry dates and user feedback)
            cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 0")
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
                    ISNULL(c.CCCODIGO, ISNULL(a.ARECODIGO, 'SIN-AREA')) as area_code,
                    ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area_name,
                    COUNT(e.NEMCODIGO) as total
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 0
                GROUP BY c.CCCODIGO, c.CCNOMBRE, a.ARECODIGO, a.ARENOMBRE
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
                if not res:
                    cursor.execute("SELECT ARENOMBRE FROM AFNAREAS WHERE RTRIM(LTRIM(ARECODIGO)) = %s", [area_code.strip()])
                    res = cursor.fetchone()
                context['area_name'] = res[0] if res else 'Área Desconocida'
                filter_sql = "WHERE e.NEMESTADO = 1 AND RTRIM(LTRIM(e.GASCODIGO)) = %s"
                params = [area_code.strip()]

            # Obtener lista de funcionarios
            filtro_tipo = self.request.GET.get('filtro', '')
            # Swapped logic: 3 is Temporal, 0 is Permanente
            clase_sql = " AND e.NEMCLAEMP = 3" if filtro_tipo == 'temporal' else " AND e.NEMCLAEMP = 0"
            
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
            
            # Swapped logic: Class 3 as Temporal
            cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 3")
            context['total_temporal'] = cursor.fetchone()[0]

            # 2. Distribución por áreas (solo temporales - Clase 3)
            query = """
                SELECT 
                    ISNULL(c.CCCODIGO, ISNULL(a.ARECODIGO, 'SIN-AREA')) as area_code,
                    ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area_name,
                    COUNT(e.NEMCODIGO) as total
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 3
                GROUP BY c.CCCODIGO, c.CCNOMBRE, a.ARECODIGO, a.ARENOMBRE
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
                        ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area,
                        v.VINNOMBRE as vinculacion,
                        cr.NCENOMBRE as cargo,
                        CASE WHEN e.NEMCLAEMP = 0 THEN 'PLANTA PERMANENTE' ELSE 'PLANTA TEMPORAL' END as tipo_planta,
                        CASE WHEN e.NEMESTADO = 1 THEN 'ACTIVO' ELSE 'INACTIVO' END as estado
                    FROM NMEMPLEA e
                    LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                    LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                    LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                    LEFT JOIN NMCARGOS cr ON RTRIM(LTRIM(e.NCECODIGO)) = RTRIM(LTRIM(cr.NCECODIGO))
                    WHERE e.NEMCODIGO = %s OR RTRIM(LTRIM(e.NEMCODIGO)) = %s
                """
                cursor.execute(query_primary, [q, q])
                columns = [col[0] for col in cursor.description]
                res = cursor.fetchone()
                
                if res:
                    context['funcionario'] = dict(zip(columns, res))
                    context['fuente'] = 'NMEMPLEA' # Nómina Principal
                else:
                    # 2. Fallback a NOMEMPLEADO (Tratando de buscar más detalles)
                    query_fallback = """
                        SELECT 
                            e.EMPCODIGO as documento,
                            (RTRIM(LTRIM(ISNULL(e.EMPNOMBRE1, ''))) + ' ' + 
                             RTRIM(LTRIM(ISNULL(e.EMPNOMBRE2, ''))) + ' ' + 
                             RTRIM(LTRIM(ISNULL(e.EMPAPELLI1, ''))) + ' ' + 
                             RTRIM(LTRIM(ISNULL(e.EMPAPELLI2, ''))) ) as nombre,
                            e.EMPFECNACI as fecha_nacimiento,
                            s.SUBNOMBRE as area,
                            'NOMEMPLEADO' as vinculacion,
                            'VERIFICAR EN FISICO' as cargo,
                            'NO ESPECIFICADO' as tipo_planta,
                            'ACTIVO' as estado
                        FROM NOMEMPLEADO e
                        LEFT JOIN NOMSUBGRU s ON e.NOMSUBGRU = s.OID
                        WHERE e.EMPCODIGO = %s OR RTRIM(LTRIM(e.EMPCODIGO)) = %s
                    """
                    cursor.execute(query_fallback, [q, q])
                    columns_f = [col[0] for col in cursor.description]
                    res_f = cursor.fetchone()
                    if res_f:
                        context['funcionario'] = dict(zip(columns_f, res_f))
                        context['fuente'] = 'NOMEMPLEADO (Hoja de Vida)'
                    else:
                        context['error'] = "No se encontró ningún funcionario con ese número de documento en Dinámica."

            # 3. Cruzar con Excel Maestro para detectar diferencias
            excel_data = get_master_excel_data()
            excel_match = next((item for item in excel_data if str(item.get('CEDULA')).strip() == q), None)
            if excel_match:
                context['excel_data'] = excel_match
                # Si no se encontró en DB, pero sí en Excel, usamos los datos del Excel
                if not context.get('funcionario'):
                    context['funcionario'] = {
                        'documento': q,
                        'nombre': excel_match.get('NOMBRE'),
                        'area': excel_match.get('AREA'),
                        'cargo': excel_match.get('CARGO'),
                        'vinculacion': excel_match.get('VINCULACION'),
                        'estado': 'EN EXCEL (FALTA DINAMICA)'
                    }
                    context['fuente'] = 'EXCEL MAESTRO 2026'

        return context

class PersonalPlantaGeneralListView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/listado_general_personal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        excel_data = get_master_excel_data()
        
        # Filtrar solo PERMANENTE según Excel
        excel_planta = [p for p in excel_data if p.get('VINCULACION') == 'PERMANENTE']
        target_ids = [str(p.get('CEDULA')).strip() for p in excel_planta]

        from django.db import connections
        with connections['readonly'].cursor() as cursor:
            # Query Dinámica para estos IDs
            placeholders = ', '.join(['%s'] * len(target_ids))
            # Padded IDs for NMEMPLEA
            padded_ids = [id.zfill(15) for id in target_ids]
            
            query = f"""
                SELECT 
                    RTRIM(LTRIM(e.NEMCODIGO)) as documento,
                    e.NEMNOMCOM as nombre,
                    e.NEMFECING as fecha_ingreso,
                    v.VINNOMBRE as vinculacion,
                    ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area
                FROM NMEMPLEA e
                LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                WHERE RTRIM(LTRIM(e.NEMCODIGO)) IN ({placeholders})
            """
            cursor.execute(query, target_ids)
            columns = [col[0] for col in cursor.description]
            db_results = {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}

        # Construir listado final basado en Excel
        funcionarios = []
        for p in excel_planta:
            cedula = str(p.get('CEDULA')).strip()
            db_data = db_results.get(cedula)
            
            funcionarios.append({
                'documento': cedula,
                'nombre': p.get('NOMBRE'),
                'area': p.get('AREA') if not db_data else db_data.get('area'),
                'vinculacion': p.get('VINCULACION'),
                'fecha_ingreso': db_data.get('fecha_ingreso') if db_data else None,
                'status_db': "OK" if db_data else "FALTA EN DINÁMICA"
            })

        context['funcionarios'] = funcionarios
        context['titulo'] = "Listado General - Planta Permanente (Según Excel)"
        context['tipo_planta'] = "Permanente"
        return context

class PersonalTemporalGeneralListView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/listado_general_personal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        excel_data = get_master_excel_data()
        
        # Filtrar solo TEMPORAL según Excel
        excel_temporal = [p for p in excel_data if p.get('VINCULACION') == 'TEMPORAL']
        target_ids = [str(p.get('CEDULA')).strip() for p in excel_temporal]

        from django.db import connections
        with connections['readonly'].cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(target_ids))
            query = f"""
                SELECT 
                    RTRIM(LTRIM(e.NEMCODIGO)) as documento,
                    e.NEMNOMCOM as nombre,
                    e.NEMFECING as fecha_ingreso,
                    v.VINNOMBRE as vinculacion,
                    ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area
                FROM NMEMPLEA e
                LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                WHERE RTRIM(LTRIM(e.NEMCODIGO)) IN ({placeholders})
            """
            cursor.execute(query, target_ids)
            columns = [col[0] for col in cursor.description]
            db_results = {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}

        funcionarios = []
        for p in excel_temporal:
            cedula = str(p.get('CEDULA')).strip()
            db_data = db_results.get(cedula)
            
            funcionarios.append({
                'documento': cedula,
                'nombre': p.get('NOMBRE'),
                'area': p.get('AREA') if not db_data else db_data.get('area'),
                'vinculacion': p.get('VINCULACION'),
                'fecha_ingreso': db_data.get('fecha_ingreso') if db_data else None,
                'status_db': "OK" if db_data else "FALTA EN DINÁMICA"
            })

        context['funcionarios'] = funcionarios
        context['titulo'] = "Listado General - Planta Temporal (Según Excel)"
        context['tipo_planta'] = "Temporal"
        return context
        context['titulo'] = "Listado General - Planta Temporal"
        context['tipo_planta'] = "Temporal"
        return context

# --- NUEVAS VISTAS BASADAS EN EXCEL (CONCILIACIÓN) ---

def get_master_excel_data():
    """Carga y cachea los datos del Excel maestro."""
    cache_key = 'th_master_excel_data'
    data = cache.get(cache_key)
    if data is None:
        path = r'C:\Users\SISTEMAS\Documents\BASE ACTUALIZADA CON CARGOS Y AREAS  04- 2026.xlsx'
        if os.path.exists(path):
            df = pd.read_excel(path)
            # Normalizar columnas
            df.columns = [c.upper().strip() for c in df.columns]
            # Convertir a lista de dicts para fácil manejo
            data = df.to_dict('records')
            cache.set(cache_key, data, 3600) # Cache por 1 hora
        else:
            data = []
    return data

class InformeConsistenciaExcelView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/informe_consistencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        excel_data = get_master_excel_data()
        
        if not excel_data:
            context['error'] = "No se pudo cargar el archivo Excel maestro en C:\\Users\\SISTEMAS\\Documents\\"
            return context

        # Obtener todos los empleados de Dinámica para comparar (por lotes o completo)
        from django.db import connections
        with connections['readonly'].cursor() as cursor:
            # Traer datos básicos de NMEMPLEA y NOMEMPLEADO para cruce
            cursor.execute("""
                SELECT 
                    RTRIM(LTRIM(e.NEMCODIGO)) as cedula,
                    e.NEMNOMCOM as nombre_dinamica,
                    CASE WHEN e.NEMCLAEMP = 0 THEN 'PERMANENTE' ELSE 'TEMPORAL' END as vinculacion_dinamica,
                    cr.NCENOMBRE as cargo_dinamica,
                    ISNULL(c.CCNOMBRE, a.ARENOMBRE) as area_dinamica
                FROM NMEMPLEA e
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN NMCARGOS cr ON RTRIM(LTRIM(e.NCECODIGO)) = RTRIM(LTRIM(cr.NCECODIGO))
                WHERE e.NEMESTADO = 1
            """)
            columns = [col[0] for col in cursor.description]
            db_employees = {row[0]: dict(zip(columns, row)) for row in cursor.fetchall()}

        # Cruce y análisis
        analisis = []
        for row in excel_data:
            cedula = str(row.get('CEDULA', '')).strip()
            db_emp = db_employees.get(cedula)
            
            estado = "OK"
            detalles = []
            
            if not db_emp:
                estado = "FALTA EN DINAMICA"
                detalles.append("El funcionario no aparece como activo en NMEMPLEA.")
            else:
                # Verificar inconsistencias
                if row.get('VINCULACION') != db_emp.get('vinculacion_dinamica'):
                    estado = "ERROR CLASIFICACION"
                    detalles.append(f"Excel: {row.get('VINCULACION')} vs Dinámica: {db_emp.get('vinculacion_dinamica')}")
                
                # Comparación de área (aproximada/basada en keywords si es necesario, por ahora exacta)
                # ... lógica adicional si hay discrepancia de nombres
            
            analisis.append({
                'cedula': cedula,
                'nombre_excel': row.get('NOMBRE'),
                'vinculacion_excel': row.get('VINCULACION'),
                'cargo_excel': row.get('CARGO'),
                'area_excel': row.get('AREA'),
                'db_data': db_emp,
                'estado': estado,
                'detalles': " | ".join(detalles)
            })

        context['analisis'] = analisis
        context['stats'] = {
            'total_excel': len(excel_data),
            'encontrados': len([a for a in analisis if a['db_data']]),
            'faltantes': len([a for a in analisis if not a['db_data']]),
        }
        return context
