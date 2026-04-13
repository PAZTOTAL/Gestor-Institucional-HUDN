from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import valida_acceso
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.apps import apps

from .models import RegistroAnestesia
from .forms import (
    RegistroAnestesiaForm, EvaluacionPreAnestesicaForm, MonitoreoForm,
    VentilacionForm, LiquidosForm, TecnicaForm, SalidaForm, ObservacionesForm
)
from .models import SignosVitales
from consultas_externas.models import Gentercer
import json
import base64
import tempfile
import os

@login_required
@valida_acceso('registro_anestesia')
def create_registro(request):
    """
    View to create a new Anesthesia Record with all sub-forms
    """
    if request.method == 'POST':
        # Main form
        registro_form = RegistroAnestesiaForm(request.POST)
        
        # Sub-models - OneToOne
        evaluacion_form = EvaluacionPreAnestesicaForm(request.POST, prefix='eval')
        monitoreo_form = MonitoreoForm(request.POST, prefix='mon')
        ventilacion_form = VentilacionForm(request.POST, prefix='vent')
        liquidos_form = LiquidosForm(request.POST, prefix='liq')
        tecnica_form = TecnicaForm(request.POST, prefix='tec')
        salida_form = SalidaForm(request.POST, prefix='sal')
        observaciones_form = ObservacionesForm(request.POST, prefix='obs')
        
        # Validate all
        if (registro_form.is_valid() and evaluacion_form.is_valid() and
            monitoreo_form.is_valid() and ventilacion_form.is_valid() and
            liquidos_form.is_valid() and tecnica_form.is_valid() and
            salida_form.is_valid() and observaciones_form.is_valid()):
            
            try:
                with transaction.atomic():
                    # 1. Save Main Record
                    registro = registro_form.save(commit=False)
                    registro.anestesiologo = request.user
                    registro.save()
                    
                    # 2. Save Sub-records
                    eval_obj = evaluacion_form.save(commit=False)
                    eval_obj.registro = registro
                    eval_obj.save()
                    
                    mon_obj = monitoreo_form.save(commit=False)
                    mon_obj.registro = registro
                    mon_obj.save()
                    
                    vent_obj = ventilacion_form.save(commit=False)
                    vent_obj.registro = registro
                    vent_obj.save()
                    
                    liq_obj = liquidos_form.save(commit=False)
                    liq_obj.registro = registro
                    liq_obj.save()
                    
                    tec_obj = tecnica_form.save(commit=False)
                    tec_obj.registro = registro
                    tec_obj.save()
                    
                    sal_obj = salida_form.save(commit=False)
                    sal_obj.registro = registro
                    sal_obj.save()
                    
                    obs_obj = observaciones_form.save(commit=False)
                    obs_obj.registro = registro
                    obs_obj.save()
                    
                    # 3. Save Chart Data
                    chart_data = request.POST.get('chart_data')
                    if chart_data:
                        points = json.loads(chart_data)
                        for pt in points:
                            SignosVitales.objects.create(
                                registro=registro,
                                hora=pt.get('time'),
                                pa_sistolica=pt.get('pas') or None,
                                pa_diastolica=pt.get('pad') or None,
                                fc=pt.get('fc') or None,
                                sao2=pt.get('spo2') or None
                            )
                    
                    messages.success(request, 'Registro de Anestesia creado correctamente.')
                    return redirect('update_registro', pk=registro.pk)
            
            except Exception as e:
                messages.error(request, f'Error al guardar: {e}')
    
    else:
        registro_form = RegistroAnestesiaForm()
        evaluacion_form = EvaluacionPreAnestesicaForm(prefix='eval')
        monitoreo_form = MonitoreoForm(prefix='mon')
        ventilacion_form = VentilacionForm(prefix='vent')
        liquidos_form = LiquidosForm(prefix='liq')
        tecnica_form = TecnicaForm(prefix='tec')
        salida_form = SalidaForm(prefix='sal')
        observaciones_form = ObservacionesForm(prefix='obs')

    context = {
        'registro_form': registro_form,
        'evaluacion_form': evaluacion_form,
        'monitoreo_form': monitoreo_form,
        'ventilacion_form': ventilacion_form,
        'liquidos_form': liquidos_form,
        'tecnica_form': tecnica_form,
        'salida_form': salida_form,
        'observaciones_form': observaciones_form,
        'title': 'Nuevo Registro de Anestesia',
        'final_chart_data': "[]"
    }
    return render(request, 'registro_anestesia/create_registro.html', context)

@login_required
@valida_acceso('registro_anestesia')
def update_registro(request, pk):
    """
    View to update an existing Anesthesia Record
    """
    registro = get_object_or_404(RegistroAnestesia, pk=pk)
    
    # Get related objects (they are OneToOne, so we access them directly)
    # Uses safe access in case somehow one is missing (though our create view prevents this)
    try:
        eval_obj = registro.evaluacion_preanestesica
        mon_obj = registro.monitoreo
        vent_obj = registro.ventilacion
        liq_obj = registro.liquidos
        tec_obj = registro.tecnica
        sal_obj = registro.salida
        obs_obj = registro.observaciones
    except Exception as e:
        messages.error(request, f"Error cargando datos relacionados: {e}")
        return redirect('admin:registro_anestesia_registroanestesia_change', pk)

    if request.method == 'POST':
        # Main form
        registro_form = RegistroAnestesiaForm(request.POST, instance=registro)
        
        # Sub-models
        evaluacion_form = EvaluacionPreAnestesicaForm(request.POST, instance=eval_obj, prefix='eval')
        monitoreo_form = MonitoreoForm(request.POST, instance=mon_obj, prefix='mon')
        ventilacion_form = VentilacionForm(request.POST, instance=vent_obj, prefix='vent')
        liquidos_form = LiquidosForm(request.POST, instance=liq_obj, prefix='liq')
        tecnica_form = TecnicaForm(request.POST, instance=tec_obj, prefix='tec')
        salida_form = SalidaForm(request.POST, instance=sal_obj, prefix='sal')
        observaciones_form = ObservacionesForm(request.POST, instance=obs_obj, prefix='obs')
        
        if (registro_form.is_valid() and evaluacion_form.is_valid() and
            monitoreo_form.is_valid() and ventilacion_form.is_valid() and
            liquidos_form.is_valid() and tecnica_form.is_valid() and
            salida_form.is_valid() and observaciones_form.is_valid()):
            
            try:
                with transaction.atomic():
                    registro_form.save()
                    evaluacion_form.save()
                    monitoreo_form.save()
                    ventilacion_form.save()
                    liquidos_form.save()
                    tecnica_form.save()
                    salida_form.save()
                    observaciones_form.save()
                    
                    # Save Chart Data (Replace existing)
                    chart_data = request.POST.get('chart_data')
                    if chart_data:
                        registro.signos_vitales.all().delete()
                        points = json.loads(chart_data)
                        for pt in points:
                            SignosVitales.objects.create(
                                registro=registro,
                                hora=pt.get('time'),
                                pa_sistolica=pt.get('pas') or None,
                                pa_diastolica=pt.get('pad') or None,
                                fc=pt.get('fc') or None,
                                sao2=pt.get('spo2') or None
                            )
                    
                    messages.success(request, 'Registro de Anestesia actualizado correctamente.')
                    return redirect('update_registro', pk=registro.pk)
            
            except Exception as e:
                messages.error(request, f'Error al actualizar: {e}')
    
    else:
        registro_form = RegistroAnestesiaForm(instance=registro)
        evaluacion_form = EvaluacionPreAnestesicaForm(instance=eval_obj, prefix='eval')
        monitoreo_form = MonitoreoForm(instance=mon_obj, prefix='mon')
        ventilacion_form = VentilacionForm(instance=vent_obj, prefix='vent')
        liquidos_form = LiquidosForm(instance=liq_obj, prefix='liq')
        tecnica_form = TecnicaForm(instance=tec_obj, prefix='tec')
        salida_form = SalidaForm(instance=sal_obj, prefix='sal')
        observaciones_form = ObservacionesForm(instance=obs_obj, prefix='obs')

    context = {
        'registro': registro, # Pass the object to check for existence in template
        'registro_form': registro_form,
        'evaluacion_form': evaluacion_form,
        'monitoreo_form': monitoreo_form,
        'ventilacion_form': ventilacion_form,
        'liquidos_form': liquidos_form,
        'tecnica_form': tecnica_form,
        'salida_form': salida_form,
        'observaciones_form': observaciones_form,
        'title': f'Editar Registro de Anestesia - {registro.paciente}'
    }
    
    # Load Chart Data for Template
    chart_qs = registro.signos_vitales.all().order_by('hora')
    chart_list = []
    for item in chart_qs:
        chart_list.append({
            'time': item.hora.strftime('%H:%M'),
            'pas': item.pa_sistolica,
            'pad': item.pa_diastolica,
            'fc': item.fc,
            'spo2': item.sao2,
            'event': '' # Events not stored yet
        })
    context['final_chart_data'] = json.dumps(chart_list)
    
    return render(request, 'registro_anestesia/create_registro.html', context)

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    # Use short circuit for absolute paths (like our temp file)
    if os.path.exists(uri):
        return uri
        
    sUrl = settings.STATIC_URL        # Typically /static/
    sRoot = settings.STATIC_ROOT      # Typically /home/userX/project/static/
    mUrl = settings.MEDIA_URL         # Typically /media/
    mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project/media/

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path

@login_required
@valida_acceso('registro_anestesia')
def print_registro_pdf(request, pk):
    registro = get_object_or_404(RegistroAnestesia, pk=pk)
    
    template_path = 'registro_anestesia/pdf_registro.html'
    context = {'registro': registro}
    
    context = {'registro': registro}
    
    if request.method == 'POST':
        chart_image = request.POST.get('chart_image')
        if chart_image:
            try:
                if 'base64,' in chart_image:
                    chart_image = chart_image.split('base64,')[1]
                
                image_data = base64.b64decode(chart_image)
                
                # Use MEDIA_ROOT for robust path handling
                charts_dir = os.path.join(settings.MEDIA_ROOT, 'charts')
                os.makedirs(charts_dir, exist_ok=True)
                
                filename = f'chart_{pk}.png'
                file_path = os.path.join(charts_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                # Pass the absolute path to template
                # link_callback will resolve this correctly because it's in MEDIA_ROOT
                context['chart_path'] = file_path
                
            except Exception as e:
                print(f"Error saving chart image: {e}")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="registro_anestesia_{registro.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
@valida_acceso('registro_anestesia')
def list_registros(request):
    from django.http import JsonResponse
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '')
    logger.info(f"list_registros called - query: '{query}'")
    logger.info(f"Headers: {dict(request.headers)}")

    
    if query:
        # Search match in Patient DB
        # Genpacien search
        Genpacien = apps.get_model('consultas_externas', 'Genpacien')
        patients_qs = Genpacien.objects.using('readonly').filter(
            Q(pacnumdoc__icontains=query) | 
            Q(pacprinom__icontains=query) |
            Q(pacpriape__icontains=query)
            # Add other name fields if necessary or use a concatenation if performance allows
        )
        patient_ids = list(patients_qs.values_list('oid', flat=True))

        registros_list = RegistroAnestesia.objects.select_related('anestesiologo').filter(
            Q(paciente_id__in=patient_ids) |
            Q(id__icontains=query)
        ).order_by('-fecha', '-created_at')

        # Smart Redirect: Always go to the latest record if found
        # if registros_list:
        #    return redirect('update_registro', pk=registros_list[0].pk)
    else:
        registros_list = RegistroAnestesia.objects.none()

    paginator = Paginator(registros_list, 10) # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Manual hydration of patient data across DBs
    registros_on_page = list(page_obj) # Force evaluation
    if registros_on_page:
        Genpacien = apps.get_model('consultas_externas', 'Genpacien')
        patient_ids = [r.paciente_id for r in registros_on_page]
        patients_map = {p.oid: p for p in Genpacien.objects.using('readonly').filter(oid__in=patient_ids)}
        for reg in registros_on_page:
            reg.paciente_obj = patients_map.get(reg.paciente_id)
            # Trick to make template use this object instead of fetching lazily
            reg.paciente = reg.paciente_obj

    context = {
        'registros': registros_on_page, # Use the hydrated list
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'title': 'Buscar Registros de Anestesia'
    }
    return render(request, 'registro_anestesia/list_registros.html', context)

@login_required
def api_recent_patients(request):
    """
    API endpoint to get recent patients from last 3 days
    Always returns JSON
    """
    from django.http import JsonResponse
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("API recent patients called")
        
        three_days_ago = datetime.now() - timedelta(days=3)
        recent_registros = RegistroAnestesia.objects.select_related('anestesiologo').filter(
            fecha__gte=three_days_ago
        ).order_by('-fecha', '-created_at')[:50]  # Limit to 50 most recent
        
        logger.info(f"Found {len(recent_registros)} recent registros")
        
        # Hydrate patient data
        Genpacien = apps.get_model('consultas_externas', 'Genpacien')
        patient_ids = [r.paciente_id for r in recent_registros]
        
        logger.info(f"Fetching {len(patient_ids)} patients from Genpacien")
        
        patients_map = {p.oid: p for p in Genpacien.objects.using('readonly').filter(oid__in=patient_ids)}
        
        logger.info(f"Found {len(patients_map)} patients in map")
        
        # Build response data
        data = []
        for reg in recent_registros:
            try:
                paciente_obj = patients_map.get(reg.paciente_id)
                
                # Get patient name safely
                if paciente_obj:
                    # Prefer textwidth if available (database calculated full name)
                    if hasattr(paciente_obj, 'textwidth') and paciente_obj.textwidth:
                         paciente_nombre = paciente_obj.textwidth
                    else:
                        try:
                            # Build full name from individual fields
                            nombre_parts = [
                                paciente_obj.pacprinom or '',
                                paciente_obj.pacsegnom or '',
                                paciente_obj.pacpriape or '',
                                paciente_obj.pacsegape or ''
                            ]
                            paciente_nombre = ' '.join(filter(None, nombre_parts)).strip() or 'Desconocido'
                        except AttributeError:
                            paciente_nombre = 'Desconocido'
                    
                    try:
                        paciente_documento = paciente_obj.pacnumdoc or 'N/A'
                    except AttributeError:
                        paciente_documento = 'N/A'
                else:
                    paciente_nombre = 'Desconocido'
                    paciente_documento = 'N/A'
                
                # Get anesthesiologist name safely
                try:
                    anestesiologo_nombre = reg.anestesiologo.get_full_name() or reg.anestesiologo.username
                except:
                    anestesiologo_nombre = 'Desconocido'
                
                data.append({
                    'id': reg.id,
                    'fecha': reg.fecha.strftime('%d/%m/%Y'),
                    'paciente_nombre': paciente_nombre,
                    'paciente_documento': paciente_documento,
                    'sala': reg.sala or '-',
                    'anestesiologo': anestesiologo_nombre
                })
            except Exception as e:
                logger.error(f"Error processing registro {reg.id}: {str(e)}")
                continue
        
        logger.info(f"Returning {len(data)} registros")
        return JsonResponse({'registros': data})
        
    except Exception as e:
        logger.error(f"Error in api_recent_patients: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e), 'registros': []}, status=500)

