import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
from django.http import HttpResponse
from core.utils_excel import process_excel_import, generate_excel_template

def importar_entidad_view(request, slug):
    """
    Vista genérica para importar datos desde Excel para las entidades de DEFENJUR.
    """
    model_map = {
        'tutelas': 'AccionTutela',
        'peticiones': 'DerechoPeticion',
        'procesos_activos': 'ProcesoJudicialActiva',
        'procesos_pasivos': 'ProcesoJudicialPasiva',
        'procesos_terminados': 'ProcesoJudicialTerminado',
        'peritajes': 'Peritaje',
        'pagos': 'PagoSentenciaJudicial',
        'sancionatorios': 'ProcesoAdministrativoSancionatorio',
        'requerimientos': 'RequerimientoEnteControl',
        'extrajudiciales': 'ProcesoExtrajudicial',
    }
    
    model_name = model_map.get(slug)
    if not model_name:
        messages.error(request, "Entidad de importación no válida.")
        return redirect('defenjur:home')
        
    model = apps.get_model('defenjur', model_name)
    
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        file = request.FILES['archivo_excel']
        preview = 'preview' in request.POST
        
        result = process_excel_import(request, model, file, preview=preview)
        
        if result['success']:
            messages.success(request, result['message'])
            if not preview:
                return redirect(f'defenjur:{slug}')
        else:
            if 'response' in result and result['response']:
                return result['response'] # Descargar CSV de errores
            messages.error(request, result['message'])
            
    return render(request, 'defenjur/importar_excel.html', {
        'model_name': model._meta.verbose_name,
        'slug': slug
    })

def descargar_plantilla_view(request, slug):
    """
    Genera y descarga una plantilla Excel para la entidad solicitada.
    """
    model_map = {
        'tutelas': 'AccionTutela',
        'peticiones': 'DerechoPeticion',
        'procesos_activos': 'ProcesoJudicialActiva',
        'procesos_pasivos': 'ProcesoJudicialPasiva',
        'procesos_terminados': 'ProcesoJudicialTerminado',
        'peritajes': 'Peritaje',
        'pagos': 'PagoSentenciaJudicial',
        'sancionatorios': 'ProcesoAdministrativoSancionatorio',
        'requerimientos': 'RequerimientoEnteControl',
        'extrajudiciales': 'ProcesoExtrajudicial',
    }
    
    model_name = model_map.get(slug)
    model = apps.get_model('defenjur', model_name)
    
    template_io = generate_excel_template(model)
    response = HttpResponse(
        template_io.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="plantilla_{slug}.xlsx"'
    return response
