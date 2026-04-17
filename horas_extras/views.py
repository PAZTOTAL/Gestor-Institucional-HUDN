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
        
        # 1. Obtener la fuente de verdad (Excel - 764 personas)
        excel_data = get_master_excel_data()
        if not excel_data:
            context['error'] = "No se pudo cargar el archivo Excel maestro."
            return context

        # 2. Obtener mapeo de áreas desde Dinámica para TODOS los activos
        # Cruza NMEMPLEA con centros de costos
        mapping = {}
        with connections['readonly'].cursor() as cursor:
            query_db = """
                SELECT 
                    RTRIM(LTRIM(e.NEMCODIGO)) as cedula,
                    ISNULL(c.CCCODIGO, ISNULL(a.ARECODIGO, 'SIN-AREA')) as area_code,
                    ISNULL(c.CCNOMBRE, ISNULL(a.ARENOMBRE, 'SIN AREA ASIGNADA')) as area_name
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                WHERE e.NEMESTADO IN (1, 2)
            """
            cursor.execute(query_db)
            for row in cursor.fetchall():
                mapping[row[0]] = {'code': row[1], 'name': row[2]}

        # 3. Cruzar y agrupar
        # Estructura: areas_dict[area_code] = {name, total, planta, temporal}
        areas_dict = {}
        
        for p in excel_data:
            cedula = str(p.get('CEDULA')).strip()
            vinc = str(p.get('VINCULACION')).upper()
            
            # Info de Dinámica o fallback
            db_info = mapping.get(cedula)
            if db_info:
                a_code = db_info['code']
                a_name = db_info['name']
            else:
                a_code = 'SIN-INFO'
                a_name = 'SIN REGISTRO EN DINÁMICA'

            if a_code not in areas_dict:
                areas_dict[a_code] = {
                    'area_code': a_code,
                    'area_name': a_name,
                    'total': 0,
                    'planta': 0,
                    'temporal': 0
                }
            
            areas_dict[a_code]['total'] += 1
            if vinc == 'PERMANENTE':
                areas_dict[a_code]['planta'] += 1
            else:
                areas_dict[a_code]['temporal'] += 1

        # 4. Convertir a lista y ordenar
        areas = sorted(areas_dict.values(), key=lambda x: x['total'], reverse=True)

        context['areas'] = areas
        context['total_empleados'] = len(excel_data)
        context['total_planta'] = sum(a['planta'] for a in areas)
        context['total_temporal'] = sum(a['temporal'] for a in areas)
        context['fecha_corte'] = timezone.now()
        return context

class PersonalAreaDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'horas_extras/reporte_personal_area_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        area_code = self.kwargs.get('area_code')
        filtro_tipo = self.request.GET.get('filtro', '').upper()
        from django.db import connections
        
        # 1. Obtener fuente de verdad (Excel)
        excel_data = get_master_excel_data()
        
        # 2. Obtener mapeo y nombres de centros de costo para el encabezado
        mapping = {}
        area_name = "Área Desconocida"
        
        with connections['readonly'].cursor() as cursor:
            # Obtener nombre del área
            if area_code != 'SIN-INFO':
                cursor.execute("SELECT CCNOMBRE FROM CTNCENCOS WHERE RTRIM(LTRIM(CCCODIGO)) = %s", [area_code])
                res = cursor.fetchone()
                if not res:
                    cursor.execute("SELECT ARENOMBRE FROM AFNAREAS WHERE RTRIM(LTRIM(ARECODIGO)) = %s", [area_code])
                    res = cursor.fetchone()
                area_name = res[0] if res else area_code
            else:
                area_name = "SIN REGISTRO EN DINÁMICA"

            # Traer info para mapeo
            cursor.execute("""
                SELECT 
                    RTRIM(LTRIM(e.NEMCODIGO)) as cedula,
                    ISNULL(c.CCCODIGO, ISNULL(a.ARECODIGO, 'SIN-AREA')) as area_code,
                    v.VINNOMBRE as vinculacion_db
                FROM NMEMPLEA e
                LEFT JOIN CTNCENCOS c ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(c.CCCODIGO))
                LEFT JOIN AFNAREAS a ON RTRIM(LTRIM(e.GASCODIGO)) = RTRIM(LTRIM(a.ARECODIGO))
                LEFT JOIN NOMVINCULA v ON e.NEMTIPCON = v.VINCODIGO
                WHERE e.NEMESTADO IN (1, 2)
            """)
            for row in cursor.fetchall():
                mapping[row[0]] = {'area': row[1], 'vinc': row[2]}

        # 3. Filtrar empleados del Excel que pertenecen a este área
        funcionarios = []
        for p in excel_data:
            cedula = str(p.get('CEDULA')).strip()
            vinc_excel = str(p.get('VINCULACION')).upper()
            
            # Determinar área en Dinámica
            emp_info = mapping.get(cedula)
            emp_area = emp_info['area'] if emp_info else 'SIN-INFO'
            
            if emp_area == area_code:
                # Aplicar filtro de tipo (Planta/Temporal) si viene de los reportes específicos
                if filtro_tipo and vinc_excel != filtro_tipo:
                    continue
                    
                funcionarios.append({
                    'documento': cedula,
                    'nombre': p.get('NOMBRE'),
                    'vinculacion': vinc_excel,
                    'vinculacion_db': emp_info['vinc'] if emp_info else 'NO REGISTRA'
                })

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
