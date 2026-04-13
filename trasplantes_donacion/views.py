from django.shortcuts import render, redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PacienteNeurocritico
from django.core.management import call_command
from django.contrib import messages
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from consultas_externas.models import Adningreso, Genpacien, Hcninterr, Hcnfolio
import pandas as pd
from django.http import HttpResponse
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
            glasgow_ingreso__in=[3, 4, 5]
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
            glasgow_ingreso__in=[3, 4, 5]
        ).order_by('-fecha_identificacion')

def sync_excel(request):
    """
    Genera el archivo Excel Neurocríticos directamente desde la base de datos HUSN,
    filtrando por Glasgow 3, 4, 5.
    """
    try:
        # 1. Consultar registros de historia clínica con Glasgow requerido
        evaluaciones = Hcninterr.objects.only('oid', 'hcnfolio', 'hciglasgow').filter(
            hciglasgow__in=[3, 4, 5]
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
            messages.warning(request, "No se encontraron pacientes que cumplan con los criterios de Glasgow (1, 2, 3, 5) en los registros recientes.")
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
    Sincroniza los pacientes ACTIVOS del hospital que cumplen con el criterio
    de Glasgow (3-5) para trasplantes y donación.
    """
    try:
        # 1. Obtener admisiones activas (pacientes que no han egresado)
        admisiones_activas = Adningreso.objects.filter(ainfecegre__isnull=True).select_related('genpacien')
        
        count = 0
        for ing in admisiones_activas:
            # 2. Buscar folios asociados a esta admisión
            folios_ids = Hcnfolio.objects.filter(adningreso=ing.oid).values_list('oid', flat=True)
            if not folios_ids:
                continue
            
            # 3. Buscar la evaluación de Glasgow más reciente que esté en el rango 3-5
            ev_reciente = Hcninterr.objects.filter(
                hcnfolio__in=folios_ids,
                hciglasgow__in=[3, 4, 5]
            ).order_by('-oid').first()

            if not ev_reciente:
                continue
                
            pac = ing.genpacien
            if not pac:
                continue
                
            # Calcular edad
            edad = None
            if pac.gpafecnac:
                diff = timezone.now().date() - pac.gpafecnac.date()
                edad = diff.days // 365
            
            sexo_str = "M" if pac.gpasexpac == 1 else "F" if pac.gpasexpac == 2 else "Indefinido"

            # 4. Crear o actualizar en la base de datos local
            PacienteNeurocritico.objects.update_or_create(
                numero_documento=pac.pacnumdoc,
                defaults={
                    'tipo_identificacion': str(pac.pactipdoc or ''),
                    'primer_nombre': pac.pacprinom or '',
                    'segundo_nombre': pac.pacsegnom or '',
                    'primer_apellido': pac.pacpriape or '',
                    'segundo_apellido': pac.pacsegape or '',
                    'fecha_nacimiento': pac.gpafecnac,
                    'sexo': sexo_str,
                    'edad': edad,
                    'fecha_ingreso': ing.ainfecing,
                    'glasgow_ingreso': int(ev_reciente.hciglasgow),
                    'diagnostico': ing.ainmotcon or 'Ingreso automático HUSN',
                    'fecha_identificacion': timezone.now(),
                    'busqueda_activa': 'SI',
                }
            )
            count += 1
            
        if count > 0:
            messages.success(request, f'Sincronización Exitosa: Se encontraron {count} pacientes activos con Glasgow 3-5.')
        else:
            messages.info(request, 'No se encontraron nuevos pacientes activos con Glasgow 3-5 en la base de datos del hospital.')
            
    except Exception as e:
        messages.error(request, f'Error al sincronizar con el Hospital: {e}')
    
    return redirect('trasplantes_donacion:dashboard')
