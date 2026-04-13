from django.http import JsonResponse
from django.apps import apps

def query_tercero(request):
    """
    API view to lookup Gentercer by document number.
    Returns JSON with third party details if found.
    """
    doc_number = request.GET.get('doc', None)
    if not doc_number:
        return JsonResponse({'found': False, 'error': 'No document provided'})
        
    try:
        Genpacien = apps.get_model('consultas_externas', 'Genpacien')
        # Using filter().first() instead of get() to avoid errors if duplicates or missing
        paciente = Genpacien.objects.filter(pacnumdoc=doc_number).first()
        
        if paciente:
            data = {
                'found': True,
                'primerNombre': paciente.pacprinom,
                'segundoNombre': paciente.pacsegnom,
                'primerApellido': paciente.pacpriape,
                'segundoApellido': paciente.pacsegape,
                'tipoDocId': paciente.pactipdoc, # Integer ID from Genpacien
                'direccion': paciente.gpadirresex if hasattr(paciente, 'gpadirresex') else '', # Check attributes
                # Add mappings as needed
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'found': False})
            
    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)})
