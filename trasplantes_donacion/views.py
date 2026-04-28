from django.shortcuts import render, redirect
from django.views.generic import ListView, TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PacienteNeurocritico
from django.core.management import call_command
from django.contrib import messages
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from consultas_externas.models import Adningreso, Genpacien, Hcninterr, Hcnfolio
import pandas as pd
from django.http import HttpResponse, JsonResponse
from io import BytesIO

class DashboardView(LoginRequiredMixin, ListView):
    model = PacienteNeurocritico
    template_name = 'trasplantes_donacion/dashboard.html'
    context_object_name = 'pacientes'
    ordering = ['-fecha_identificacion', '-id']
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas rápidas
        context['total_pacientes'] = PacienteNeurocritico.objects.count()
        context['alertados'] = PacienteNeurocritico.objects.filter(
            glasgow_ingreso__gte=1, glasgow_ingreso__lte=5
        ).count()
        context['donantes_efectivos'] = PacienteNeurocritico.objects.filter(donante_efectivo='SI').count()
        return context

class AlertasView(LoginRequiredMixin, ListView):
    model = PacienteNeurocritico
    template_name = 'trasplantes_donacion/alertas.html'
    context_object_name = 'pacientes_criticos'

    def get_queryset(self):
        # Criterios de alerta: Glasgow 1, 2, 3 o 5
        return PacienteNeurocritico.objects.filter(
            glasgow_ingreso__gte=1, glasgow_ingreso__lte=5
        ).order_by('-fecha_identificacion')

def sync_excel(request):
    """
    Genera el archivo Excel Neurocríticos directamente desde la base de datos HUSN,
    filtrando por Glasgow 3, 4, 5.
    """
    try:
        # 1. Consultar registros de historia clínica con Glasgow requerido
        evaluaciones = Hcninterr.objects.using('readonly').only('oid', 'hcnfolio', 'hciglasgow').filter(
            hciglasgow__gte=1, hciglasgow__lte=5
        ).order_by('-oid')[:500] 
        
        data = []
        for ev in evaluaciones:
            folio_oid = ev.hcnfolio
            if not folio_oid: continue
            
            folio = Hcnfolio.objects.only('oid', 'genpacien', 'adningreso').filter(oid=folio_oid).first()
            if not folio: continue
            
            pac = Genpacien.objects.only(
                'oid', 'pacnumdoc', 'pactipdoc', 'pacprinom', 'pacsegnom', 
                'pacpriape', 'pacsegape', 'gpafecnac', 'gpasexpac'
            ).filter(oid=folio.genpacien).first()
            
            ing = Adningreso.objects.only(
                'oid', 'ainfecing', 'ainmotcon', 'genpacien'
            ).filter(oid=folio.adningreso).first()
            
            if not pac or not ing: continue

            # Calcular edad
            edad = None
            if pac.gpafecnac:
                diff = timezone.now().date() - pac.gpafecnac.date()
                edad = diff.days // 365

            # -- ADICIÓN: Actualizar base de datos local --
            PacienteNeurocritico.objects.update_or_create(
                numero_documento=pac.pacnumdoc,
                defaults={
                    'tipo_identificacion': pac.pactipdoc,
                    'primer_nombre': pac.pacprinom or '',
                    'segundo_nombre': pac.pacsegnom or '',
                    'primer_apellido': pac.pacpriape or '',
                    'segundo_apellido': pac.pacsegape or '',
                    'fecha_nacimiento': pac.gpafecnac,
                    'sexo': "M" if pac.gpasexpac == 1 else "F" if pac.gpasexpac == 2 else "I",
                    'edad': edad,
                    'fecha_ingreso': ing.ainfecing,
                    'glasgow_ingreso': int(ev.hciglasgow),
                    'diagnostico': ing.ainmotcon or 'Evaluación Neurocrítica',
                    'fecha_identificacion': timezone.now(),
                    'busqueda_activa': 'SI',
                }
            )

            # Construir fila para el Excel (Misma estructura que el archivo original)
            row = {
                'ITEM': ev.oid,
                'FECHA DE IDENTIFICACION': timezone.now().date(),
                'BUSQUEDA ACTIVA': 'SI',
                'BUSQUEDA PASIVA ': 'NO',
                'SERVICIO': 'HUSN', # Podría extraerse de ing.ainservicio si existe
                'PACIENTE INTUBADO (SI/NO)': 'SI' if ev.hciglasgow <= 8 else 'NO',
                'TIPO DE IDENTIFICACION': pac.pactipdoc,
                'NUMERO DE DOCUMENTO ': pac.pacnumdoc,
                'PRIMER NOMBRE': pac.pacprinom,
                'SEGUNDO NOMBRE': pac.pacsegnom,
                'PRIMER APELLIDO': pac.pacpriape,
                'SEGUNDO APELLIDO': pac.pacsegape,
                'FECHA DE NACIMIENTO': pac.gpafecnac.date() if pac.gpafecnac else None,
                'SEXO': "M" if pac.gpasexpac == 1 else "F" if pac.gpasexpac == 2 else "I",
                'EDAD': edad,
                'OCUPACION': '',
                'ETNIA ': '',
                'MUNICIPIO DE RESIDENCIA ': '',
                'EAPB': '',
                'FECHA DE INGRESO': ing.ainfecing.date() if ing.ainfecing else None,
                'GLASGOW DE INGRESO ': int(ev.hciglasgow),
                'CODIGO CIE10': '',
                'DIAGNOSTICO': ing.ainmotcon or 'Evaluación Neurocrítica',
                'PACIENTE ALERTADO SI /NO ': 'SI',
                'FECHA Y HORA DE ALERTA A CRT': None,
                'CAUSA DE NO ALERTA ': '',
                'CODIGO DE VOLUNTADES ANTICIPIDAS ': '',
                'DX DE MUERTE ENCEFALICA (SI/NO)': 'NO',
                'FECHA DE DIAGNOSTICO DE MUERTE ENCEFALICA Y HORA ': None,
                'PACIENTE LEGALIZADO SI/NO': 'NO',
                'CAUSA DE NO LEGALIZACION': '',
                ' FECHA DE LEGALIZACION': None,
                'DONANTE EFECTIVO SI/NO': 'NO',
                'CAUSA DE NO SER DONANTE EFECTIVO ': '',
                'ESTADO VITAL EGRESO ': 'VIVO',
                'FECHA DE EGRESO ': None,
                'ORGANOS RECATADOS ': '',
                'MEDICO QUE ALERTA ': '',
                'MEDICO QUE NO ALERTA ': '',
                'OBSERVACIONES ': 'Generado automáticamente desde Sistema Central',
            }
            data.append(row)

        if not data:
            messages.warning(request, "No se encontraron pacientes que cumplan con los criterios de Glasgow (1-5) en los registros recientes.")
            return redirect('trasplantes_donacion:dashboard')

        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # --- NUEVO: Guardar físicamente en el servidor (H:\HUDN) ---
        try:
            path_h = r'H:\HUDN\Base_Datos_NeuroCriticos_Actualizado.xlsx'
            df.to_excel(path_h, index=False)
            # Nota: Los mensajes de Django pueden no verse si se devuelve un archivo directamente,
            # pero el archivo quedará guardado en el disco.
        except Exception as e:
            # Si falla el guardado en disco, al menos intentamos que descargue
            pass

        # Generar Excel para descarga en navegador
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Neurocriticos')
        
        output.seek(0)
        
        # Nombre del archivo para descarga
        filename = f"Base_Datos_NeuroCriticos_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

    except Exception as e:
        messages.error(request, f'Error al generar el reporte Excel: {e}')
        return redirect('trasplantes_donacion:dashboard')
def sync_husn(request):
    """
    Sincroniza los pacientes ACTIVOS del hospital con diagnósticos
    neurocerebrales (CIE10: G9x, I6x, S06, R40, G40, G41) relevantes
    para el seguimiento de trasplantes y donación.
    """
    from django.db import connections

    try:
        cursor = connections['readonly'].cursor()

        # Buscar pacientes activos con diagnósticos neurocerebrales
        # CIE10: G9x (cerebro), I6x (cerebrovascular), S06 (trauma craneal),
        #        R40 (coma/somnolencia), G40-G41 (epilepsia)
        cursor.execute("""
            SELECT TOP 10
                dp.GENDIAGNO,
                dg.DIACODIGO,
                dg.DIANOMBRE,
                f.ADNINGRESO,
                f.GENPACIEN,
                a.AINFECING,
                a.AINMOTCON,
                p.PACNUMDOC,
                p.PACTIPDOC,
                p.PACPRINOM,
                p.PACSEGNOM,
                p.PACPRIAPE,
                p.PACSEGAPE,
                p.GPAFECNAC,
                p.GPASEXPAC
            FROM HCNDIAPAC dp
            INNER JOIN GENDIAGNO dg ON dp.GENDIAGNO = dg.OID
            INNER JOIN HCNFOLIO f ON dp.HCNFOLIO = f.OID
            INNER JOIN ADNINGRESO a ON f.ADNINGRESO = a.OID
            INNER JOIN GENPACIEN p ON f.GENPACIEN = p.OID
            WHERE a.AINFECEGRE IS NULL
              AND (
                dg.DIACODIGO LIKE 'G9[0-9]%'
                OR dg.DIACODIGO LIKE 'I6[0-9]%'
                OR dg.DIACODIGO LIKE 'S06%'
                OR dg.DIACODIGO LIKE 'R40%'
                OR dg.DIACODIGO LIKE 'G4[0-1]%'
              )
              AND p.PACNUMDOC IS NOT NULL
            ORDER BY dp.OID DESC
        """)

        rows = cursor.fetchall()
        count = 0
        errores = 0
        procesados = set()

        for row in rows:
            try:
                (diag_oid, cie10_code, cie10_nombre, ing_oid, pac_oid,
                 fecha_ing, motivo, numdoc, tipdoc, prinom, segnom,
                 priape, segape, fecnac, sexpac) = row

                numdoc_str = str(numdoc).strip()
                if numdoc_str in procesados:
                    continue
                procesados.add(numdoc_str)

                # Calcular edad
                edad = None
                if fecnac:
                    try:
                        fec = fecnac.date() if hasattr(fecnac, 'date') else fecnac
                        diff = timezone.now().date() - fec
                        edad = diff.days // 365
                    except Exception:
                        pass

                sexo_str = "M" if sexpac == 1 else "F" if sexpac == 2 else "Indefinido"
                cie10_str = f"{(cie10_code or '').strip()}"
                diag_str = f"{(cie10_nombre or motivo or 'Diagnóstico neurocrítico').strip()}"

                # Guardar en la base de datos local
                PacienteNeurocritico.objects.update_or_create(
                    numero_documento=numdoc_str,
                    defaults={
                        'tipo_identificacion': str(tipdoc or ''),
                        'primer_nombre': (prinom or '').strip(),
                        'segundo_nombre': (segnom or '').strip(),
                        'primer_apellido': (priape or '').strip(),
                        'segundo_apellido': (segape or '').strip(),
                        'fecha_nacimiento': fecnac,
                        'sexo': sexo_str,
                        'edad': edad,
                        'fecha_ingreso': fecha_ing,
                        'glasgow_ingreso': 0,
                        'codigo_cie10': cie10_str,
                        'diagnostico': diag_str,
                        'fecha_identificacion': timezone.now(),
                        'busqueda_activa': 'SI',
                    }
                )
                count += 1

            except Exception:
                errores += 1
                continue

        if count > 0:
            msg = f'✅ Sincronización Exitosa: {count} pacientes neurocríticos activos cargados.'
            if errores > 0:
                msg += f' ({errores} omitidos por errores)'
            messages.success(request, msg)
        else:
            msg = 'No se encontraron pacientes activos con diagnósticos neurocerebrales.'
            if errores > 0:
                msg += f' ({errores} registros con errores)'
            messages.warning(request, msg)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        messages.error(request, f'Error al sincronizar: {e}')

    return redirect('trasplantes_donacion:dashboard')

def historia_clinica_api(request, pk):
    """
    Retorna datos de historia clínica del paciente desde la base hospitalaria.
    Incluye: diagnósticos, evaluaciones, notas de enfermería, medicamentos.
    """
    from django.db import connections

    paciente = PacienteNeurocritico.objects.filter(pk=pk).first()
    if not paciente:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

    data = {
        'paciente': {
            'nombre': f"{paciente.primer_nombre} {paciente.segundo_nombre or ''} {paciente.primer_apellido} {paciente.segundo_apellido or ''}".strip(),
            'documento': f"{paciente.tipo_identificacion} {paciente.numero_documento}",
            'sexo': paciente.sexo,
            'edad': paciente.edad,
            'fecha_nacimiento': paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '-',
            'fecha_ingreso': paciente.fecha_ingreso.strftime('%d/%m/%Y %H:%M') if paciente.fecha_ingreso else '-',
            'glasgow': paciente.glasgow_ingreso,
            'cie10': paciente.codigo_cie10 or '-',
            'diagnostico_principal': paciente.diagnostico or '-',
            'servicio': paciente.servicio or '-',
            'busqueda_activa': paciente.busqueda_activa or '-',
        },
        'diagnosticos': [],
        'evaluaciones': [],
        'notas_enfermeria': [],
        'medicamentos': [],
    }

    try:
        cursor = connections['readonly'].cursor()

        # Buscar el ingreso activo de este paciente
        cursor.execute("""
            SELECT TOP 1 a.OID
            FROM ADNINGRESO a
            INNER JOIN GENPACIEN p ON a.GENPACIEN = p.OID
            WHERE p.PACNUMDOC = %s AND a.AINFECEGRE IS NULL
            ORDER BY a.AINFECING DESC
        """, [paciente.numero_documento])
        ing_row = cursor.fetchone()

        if not ing_row:
            return JsonResponse(data)

        ing_oid = ing_row[0]

        # Obtener folios del ingreso
        cursor.execute("""
            SELECT OID FROM HCNFOLIO WHERE ADNINGRESO = %s ORDER BY OID DESC
        """, [ing_oid])
        folios = [r[0] for r in cursor.fetchall()]

        if not folios:
            return JsonResponse(data)

        folio_ids = ','.join([str(f) for f in folios])

        # 1. DIAGNÓSTICOS
        cursor.execute(f"""
            SELECT dg.DIACODIGO, dg.DIANOMBRE, dp.HCPDIAPRIN
            FROM HCNDIAPAC dp
            LEFT JOIN GENDIAGNO dg ON dp.GENDIAGNO = dg.OID
            WHERE dp.HCNFOLIO IN ({folio_ids})
            ORDER BY dp.HCPDIAPRIN DESC, dp.OID DESC
        """)
        seen_diag = set()
        for r in cursor.fetchall():
            codigo = (r[0] or '').strip()
            nombre = (r[1] or '').strip()
            key = f"{codigo}-{nombre}"
            if key in seen_diag:
                continue
            seen_diag.add(key)
            data['diagnosticos'].append({
                'codigo': codigo,
                'nombre': nombre,
                'principal': bool(r[2]),
            })

        # 2. EVALUACIONES / INTERCONSULTAS
        cursor.execute(f"""
            SELECT OID, HCIGLASGOW, HCIFRCCRD, HCIFRCRES, HCITEMPER, HCISATURA,
                   CAST(HCIDETRES AS NVARCHAR(MAX)),
                   CAST(HCITRATAM AS NVARCHAR(MAX)),
                   CAST(HCIANAOBJ AS NVARCHAR(MAX))
            FROM HCNINTERR
            WHERE HCNFOLIO IN ({folio_ids})
            ORDER BY OID DESC
        """)
        for r in cursor.fetchall():
            data['evaluaciones'].append({
                'glasgow': float(r[1]) if r[1] else None,
                'fc': float(r[2]) if r[2] else None,
                'fr': float(r[3]) if r[3] else None,
                'temperatura': float(r[4]) if r[4] else None,
                'saturacion': float(r[5]) if r[5] else None,
                'detalle': (r[6] or '')[:500].strip(),
                'tratamiento': (r[7] or '')[:500].strip(),
                'analisis': (r[8] or '')[:500].strip(),
            })

        # 3. NOTAS DE ENFERMERÍA
        cursor.execute(f"""
            SELECT n.HCRHORREG, n.HCNTITULO,
                   CAST(n.HCNSUBOBJ AS NVARCHAR(MAX)),
                   CAST(n.HCNANAPLAN AS NVARCHAR(MAX))
            FROM HCNNOTENF n
            INNER JOIN HCNFOLIO f ON n.HCNREGENF = f.OID
            WHERE f.ADNINGRESO = %s
            ORDER BY n.OID DESC
        """, [ing_oid])
        for r in cursor.fetchall():
            data['notas_enfermeria'].append({
                'fecha': r[0].strftime('%d/%m/%Y %H:%M') if r[0] else '-',
                'titulo': (r[1] or '').strip(),
                'contenido': (r[2] or '')[:500].strip(),
                'plan': (r[3] or '')[:500].strip(),
            })

        # 4. MEDICAMENTOS
        cursor.execute(f"""
            SELECT cm.HCRHORREG, cm.HCDOSIS, cm.HCOBSERVA, cm.HCCANTIDAD
            FROM HCNCONMED cm
            INNER JOIN HCNFOLIO f ON cm.HCNMEDPAC = f.OID
            WHERE f.ADNINGRESO = %s
            ORDER BY cm.OID DESC
        """, [ing_oid])
        for r in cursor.fetchall():
            data['medicamentos'].append({
                'fecha': r[0].strftime('%d/%m/%Y %H:%M') if r[0] else '-',
                'dosis': (r[1] or '').strip() if r[1] else '-',
                'observacion': (r[2] or '').strip() if r[2] else '-',
                'cantidad': float(r[3]) if r[3] else None,
            })

    except Exception as e:
        data['error_detalle'] = str(e)

    return JsonResponse(data)


class PacienteUpdateView(LoginRequiredMixin, UpdateView):
    model = PacienteNeurocritico
    template_name = 'trasplantes_donacion/paciente_form.html'
    fields = [
        'paciente_intubado', 'paciente_alertado', 'fecha_hora_alerta_crt', 
        'causa_no_alerta', 'voluntades_anticipadas', 'dx_muerte_encefalica', 
        'fecha_diagnostico_me_hora', 'paciente_legalizado', 'causa_no_legalizacion', 
        'fecha_legalizacion', 'donante_efectivo', 'causa_no_donante_efectivo', 
        'estado_vital_egreso', 'fecha_egreso', 'organos_recatados', 
        'medico_alerta', 'medico_no_alerta', 'observaciones'
    ]
    
    def get_success_url(self):
        from django.urls import reverse
        return reverse('trasplantes_donacion:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Gestionar Proceso - {self.object.primer_nombre} {self.object.primer_apellido}"
        return context

def reporte_diario(request):
    """
    Reporte de pacientes con cualquier registro de Glasgow el día de hoy.
    Busca en Interconsultas (HCNINTERR) y Triage (HCNTCENTURED).
    """
    from django.db import connections
    from django.utils import timezone
    hoy = timezone.now().date()
    
    evaluaciones = []
    pacientes_unicos = set()

    # 1. Buscar en HCNINTERR (Interconsultas/Evaluaciones)
    # Usamos raw SQL para mayor control sobre los joins en la DB readonly
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.PACNUMDOC,
                    p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    i.HCIGLASGOW,
                    f.HCFECFOL,
                    'EVALUACIÓN' as ORIGEN
                FROM HCNINTERR i
                INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
                INNER JOIN GENPACIEN p ON f.GENPACIEN = p.OID
                WHERE CAST(f.HCFECFOL AS DATE) = CAST(GETDATE() AS DATE)
                AND i.HCIGLASGOW IS NOT NULL
            """)
            rows = cursor.fetchall()
            for row in rows:
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                
                edad = '?'
                if fecnac:
                    try:
                        edad = (timezone.now().date() - fecnac.date()).days // 365
                    except: pass

                pacientes_unicos.add(doc)
                evaluaciones.append({
                    'pac_doc': doc,
                    'pac_nombre': nombre,
                    'pac_sexo': 'M' if sex == 1 else 'F',
                    'pac_edad': edad,
                    'glasgow': int(glasgow),
                    'fecha': fecha,
                    'especialidad': origen
                })
    except Exception as e:
        print(f"Error en query Interconsultas: {e}")

    # 2. Buscar en HCNTCENTURED (Triage)
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.PACNUMDOC,
                    p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    t.HCNGLASGOW,
                    t.HCRHORREG,
                    'TRIAGE' as ORIGEN
                FROM HCNTCENTURED t
                INNER JOIN GENPACIEN p ON t.GENPACIEN = p.OID
                WHERE CAST(t.HCRHORREG AS DATE) = CAST(GETDATE() AS DATE)
                AND t.HCNGLASGOW IS NOT NULL
            """)
            rows = cursor.fetchall()
            for row in rows:
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                
                edad = '?'
                if fecnac:
                    try:
                        edad = (timezone.now().date() - fecnac.date()).days // 365
                    except: pass

                pacientes_unicos.add(doc)
                evaluaciones.append({
                    'pac_doc': doc,
                    'pac_nombre': nombre,
                    'pac_sexo': 'M' if sex == 1 else 'F',
                    'pac_edad': edad,
                    'glasgow': int(glasgow),
                    'fecha': fecha,
                    'especialidad': origen
                })
    except Exception as e:
        print(f"Error en query Triage (HCNTCENTURED): {e}")

    # 3. Buscar en HCNTRIAGE (Triage General)
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.PACNUMDOC,
                    p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    COALESCE(t.HCTNOGLASA, t.HCTNOGLASP) as GLASGOW,
                    t.HCTFECTRI,
                    'TRIAGE GENERAL' as ORIGEN
                FROM HCNTRIAGE t
                INNER JOIN GENPACIEN p ON t.GENPACIEN = p.OID
                WHERE CAST(t.HCTFECTRI AS DATE) = CAST(GETDATE() AS DATE)
                AND (t.HCTNOGLASA IS NOT NULL OR t.HCTNOGLASP IS NOT NULL)
            """)
            rows = cursor.fetchall()
            for row in rows:
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                
                edad = '?'
                if fecnac:
                    try:
                        edad = (timezone.now().date() - fecnac.date()).days // 365
                    except: pass

                pacientes_unicos.add(doc)
                evaluaciones.append({
                    'pac_doc': doc,
                    'pac_nombre': nombre,
                    'pac_sexo': 'M' if sex == 1 else 'F',
                    'pac_edad': edad,
                    'glasgow': int(glasgow) if glasgow else 0,
                    'fecha': fecha,
                    'especialidad': origen
                })
    except Exception as e:
        print(f"Error en query Triage General (HCNTRIAGE): {e}")

    # Ordenar por fecha descendente
    evaluaciones.sort(key=lambda x: x['fecha'], reverse=True)

    return render(request, 'trasplantes_donacion/reporte_diario.html', {
        'hoy': hoy,
        'evaluaciones': evaluaciones,
        'pacientes_unicos': len(pacientes_unicos),
        'alertados': PacienteNeurocritico.objects.filter(glasgow_ingreso__gte=1, glasgow_ingreso__lte=5).count()
    })

def reporte_mensual(request):
    """
    Reporte de pacientes con Glasgow 1 a 5 en un mes y año específicos.
    """
    from django.db import connections
    from django.utils import timezone
    import datetime

    # Obtener el mes y año del request, por defecto el mes/año actual
    hoy = timezone.now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    mes_str = request.GET.get('mes', str(mes_actual))
    anio_str = request.GET.get('anio', str(anio_actual))
    
    try:
        mes = int(mes_str)
        anio = int(anio_str)
    except ValueError:
        mes = mes_actual
        anio = anio_actual

    evaluaciones = []
    pacientes_unicos = set()

    # Filtro SQL para el mes y año, y Glasgow entre 1 y 5
    # HCNINTERR (Evaluaciones/Interconsultas)
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    p.PACNUMDOC, p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    i.HCIGLASGOW, f.HCFECFOL, 'EVALUACIÓN' as ORIGEN
                FROM HCNINTERR i
                INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
                INNER JOIN GENPACIEN p ON f.GENPACIEN = p.OID
                WHERE YEAR(f.HCFECFOL) = {anio} AND MONTH(f.HCFECFOL) = {mes}
                AND i.HCIGLASGOW >= 1 AND i.HCIGLASGOW <= 5
            """)
            for row in cursor.fetchall():
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                edad = '?'
                if fecnac:
                    try: edad = (hoy - fecnac.date()).days // 365
                    except: pass
                pacientes_unicos.add(doc)
                evaluaciones.append({'pac_doc': doc, 'pac_nombre': nombre, 'pac_sexo': 'M' if sex == 1 else 'F', 'pac_edad': edad, 'glasgow': int(glasgow), 'fecha': fecha, 'especialidad': origen})
    except Exception as e:
        print(f"Error query Mensual HCNINTERR: {e}")

    # HCNTCENTURED (Triage Urgencias)
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    p.PACNUMDOC, p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    t.HCNGLASGOW, t.HCETFECHAING, 'TRIAGE URGENCIAS' as ORIGEN
                FROM HCNTCENTURED t
                INNER JOIN GENPACIEN p ON t.GENPACIEN = p.OID
                WHERE YEAR(t.HCETFECHAING) = {anio} AND MONTH(t.HCETFECHAING) = {mes}
                AND t.HCNGLASGOW >= 1 AND t.HCNGLASGOW <= 5
            """)
            for row in cursor.fetchall():
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                edad = '?'
                if fecnac:
                    try: edad = (hoy - fecnac.date()).days // 365
                    except: pass
                pacientes_unicos.add(doc)
                evaluaciones.append({'pac_doc': doc, 'pac_nombre': nombre, 'pac_sexo': 'M' if sex == 1 else 'F', 'pac_edad': edad, 'glasgow': int(glasgow), 'fecha': fecha, 'especialidad': origen})
    except Exception as e:
        print(f"Error query Mensual HCNTCENTURED: {e}")

    # HCNTRIAGE (Triage General)
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    p.PACNUMDOC, p.PACPRINOM, p.PACSEGNOM, p.PACPRIAPE, p.PACSEGAPE,
                    p.GPASEXPAC, p.GPAFECNAC,
                    COALESCE(t.HCTNOGLASA, t.HCTNOGLASP) as GLASGOW,
                    t.HCTFECTRI, 'TRIAGE GENERAL' as ORIGEN
                FROM HCNTRIAGE t
                INNER JOIN GENPACIEN p ON t.GENPACIEN = p.OID
                WHERE YEAR(t.HCTFECTRI) = {anio} AND MONTH(t.HCTFECTRI) = {mes}
                AND (
                    (t.HCTNOGLASA >= 1 AND t.HCTNOGLASA <= 5)
                    OR 
                    (t.HCTNOGLASP >= 1 AND t.HCTNOGLASP <= 5)
                )
            """)
            for row in cursor.fetchall():
                doc, p1, p2, a1, a2, sex, fecnac, glasgow, fecha, origen = row
                nombre = f"{p1 or ''} {p2 or ''} {a1 or ''} {a2 or ''}".strip()
                edad = '?'
                if fecnac:
                    try: edad = (hoy - fecnac.date()).days // 365
                    except: pass
                if glasgow:
                    pacientes_unicos.add(doc)
                    evaluaciones.append({'pac_doc': doc, 'pac_nombre': nombre, 'pac_sexo': 'M' if sex == 1 else 'F', 'pac_edad': edad, 'glasgow': int(glasgow), 'fecha': fecha, 'especialidad': origen})
    except Exception as e:
        print(f"Error query Mensual HCNTRIAGE: {e}")

    # Ordenar por fecha descendente
    evaluaciones.sort(key=lambda x: x['fecha'], reverse=True)

    meses = [
        {'id': 1, 'nombre': 'Enero'}, {'id': 2, 'nombre': 'Febrero'}, {'id': 3, 'nombre': 'Marzo'},
        {'id': 4, 'nombre': 'Abril'}, {'id': 5, 'nombre': 'Mayo'}, {'id': 6, 'nombre': 'Junio'},
        {'id': 7, 'nombre': 'Julio'}, {'id': 8, 'nombre': 'Agosto'}, {'id': 9, 'nombre': 'Septiembre'},
        {'id': 10, 'nombre': 'Octubre'}, {'id': 11, 'nombre': 'Noviembre'}, {'id': 12, 'nombre': 'Diciembre'}
    ]
    anios = [anio_actual, anio_actual - 1, anio_actual - 2]

    return render(request, 'trasplantes_donacion/reporte_mensual.html', {
        'evaluaciones': evaluaciones,
        'pacientes_unicos': len(pacientes_unicos),
        'alertados': PacienteNeurocritico.objects.filter(glasgow_ingreso__gte=1, glasgow_ingreso__lte=5).count(),
        'mes_seleccionado': mes,
        'anio_seleccionado': anio,
        'meses': meses,
        'anios': anios
    })

