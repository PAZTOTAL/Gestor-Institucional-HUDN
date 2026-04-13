import json, traceback, logging
logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import DocumentoConsentimiento, FirmaBiometrica
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
import io
from django.db.models import Q
from HospitalManagement.api_views import calculate_age
# Importar modelos de otras apps (Read-Only)
from consultas_externas.models import Genpacien, Adningreso, Hcnfolio, Genareser, Hpndefcam
from usuarios.models import PerfilUsuario

@login_required
def listar_documentos(request):
    """
    Lista todos los documentos disponibles.
    Se eliminó la restricción de 'firmados' para permitir múltiples firmas.
    """
    documentos = DocumentoConsentimiento.objects.filter(activo=True).order_by('titulo')
    return render(request, 'consentimientos/lista.html', {
        'documentos': documentos,
    })

import re

@login_required
def detalle_documento(request, pk):
    documento = get_object_or_404(DocumentoConsentimiento, pk=pk)
    
    # Extraer placeholders tipo {{ campo }}
    placeholders = re.findall(r'\{\{\s*(\w+)\s*\}\}', documento.contenido)
    # Eliminar duplicados manteniendo orden
    placeholders = list(dict.fromkeys(placeholders))
    
    # Verificar si el médico actual tiene firma registrada
    from .models import FirmaFuncionario
    firma_oficial = FirmaFuncionario.objects.filter(user=request.user, activo=True).first()
    
    return render(request, 'consentimientos/detalle.html', {
        'documento': documento,
        'placeholders': placeholders,
        'has_official_signature': firma_oficial is not None,
        'official_signature': firma_oficial.firma_data if firma_oficial else None
    })

@csrf_exempt
@login_required
def guardar_firma_documento(request, pk):
    try:
        if request.method == 'POST':
            documento = get_object_or_404(DocumentoConsentimiento, pk=pk)
            
            try:
                data = json.loads(request.body)
                firma_base64 = data.get('firma_base64')
                firma_medico_base64 = data.get('firma_medico_base64')
                firma_testigo_base64 = data.get('firma_testigo_base64')
                datos_form = data.get('datos_formulario', {})
                
                # Datos de trazabilidad HUDN
                ingreso_id = data.get('ingreso_id')
                pac_oid = data.get('paciente_oid')
                folio = data.get('folio')
                historia = data.get('historia_clinica') or datos_form.get('identificacion')

                if not firma_base64:
                    return JsonResponse({'status': 'error', 'message': 'No se recibió la imagen de la firma del paciente'}, status=400)
                
                # REGLA: Si el médico no firmó manualmente, intentar usar su firma registrada
                if not firma_medico_base64:
                    from .models import FirmaFuncionario
                    f_oficial = FirmaFuncionario.objects.filter(user=request.user, activo=True).first()
                    if f_oficial:
                        firma_medico_base64 = f_oficial.firma_data
                    
                # Guardar la firma y los datos en el modelo
                FirmaBiometrica.objects.create(
                    documento=documento,
                    user=request.user,
                    ingreso_id=ingreso_id,
                    paciente_oid=pac_oid,
                    folio=folio,
                    historia_clinica=historia,
                    firma_data=firma_base64,
                    firma_medico_data=firma_medico_base64,
                    firma_testigo_data=firma_testigo_base64,
                    datos_formulario=json.dumps(datos_form),
                    metadata_seguridad=json.dumps({
                        'ip': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT'),
                        'tunnel': request.get_host(),
                        'metodo': 'multi_signature_liberada_v2'
                    })
                )
                return JsonResponse({'status': 'ok'})
                
            except Exception as e:
                logger.error(f"Error guardando firma: {str(e)}\n{traceback.format_exc()}")
                return JsonResponse({'status': 'error', 'message': f'Error procesando la firma: {str(e)}'}, status=400)
                
        return JsonResponse({'status': 'error', 'message': 'Método no permitido. Solo POST.'}, status=405)
    except Exception as e:
        error_detailed = traceback.format_exc()
        print(f"[ERROR 500 GUARDAR_FIRMA]: {error_detailed}")
@login_required
def descargar_pdf_firmado(request, pk):
    firma = get_object_or_404(FirmaBiometrica, pk=pk)
    documento = firma.documento
    
    # Reemplazar placeholders en el contenido con los datos reales
    datos_json = json.loads(firma.datos_formulario)
    contenido_final = documento.contenido
    for key, value in datos_json.items():
        contenido_final = contenido_final.replace(f'{{{{ {key} }}}}', str(value))
        contenido_final = contenido_final.replace(f'{{{{{key}}}}}', str(value))
    
    # Normalizar datos para evitar errores de VariableDoesNotExist en el template
    datos_normalizados = datos_json.copy()
    if 'identificacion_paciente' in datos_normalizados and 'identificacion' not in datos_normalizados:
        datos_normalizados['identificacion'] = datos_normalizados['identificacion_paciente']
    elif 'identificacion' in datos_normalizados and 'identificacion_paciente' not in datos_normalizados:
        datos_normalizados['identificacion_paciente'] = datos_normalizados['identificacion']
    
    # Preparar HTML para PDF
    html_content = render_to_string('consentimientos/pdf_template.html', {
        'documento': documento,
        'firma': firma,
        'contenido_final': contenido_final,
        'datos': datos_normalizados
    })
    
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_content.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="consentimiento_{firma.id}.pdf"'
        return response
    
    return HttpResponse("Error generando PDF", status=500)

@login_required
def api_pacientes_activos(request):
    """
    Retorna la lista de pacientes con ingresos activos (ainestado=1).
    Filtra por área si el usuario no es ADMINISTRADOR.
    """
    # 1. Determinar nivel de acceso
    perfil = PerfilUsuario.objects.filter(user=request.user).first()
    is_admin = perfil and perfil.categoria == 'ADMIN'
    
    # 2. Consultar ingresos activos
    # aynestado=1 (Activo)
    # Usar .only() para eficiencia si es necesario
    ingresos_query = Adningreso.objects.using('readonly').filter(ainestado=1).select_related('genpacien').order_by('-ainfecing')
    
    # Filtrar por área si no es admin
    if not is_admin:
        # Aquí buscaríamos el área asociada al usuario.
        # Por ahora devolveremos los últimos 100 del sistema.
        ingresos_query = ingresos_query[:100]
    else:
        ingresos_query = ingresos_query[:500]

    results = []
    for ing in ingresos_query:
        pac = ing.genpacien
        if not pac: continue
        
        # Obtener cama/ubicación (simplificado)
        cama_obj = Hpndefcam.objects.using('readonly').filter(oid=ing.hpndefcam).first()
        cama_nombre = cama_obj.hcacodigo if cama_obj else "S/C"
        
        # Obtener nombre de área para mostrar
        area_nombre = "HOSP"
        if ing.genareser:
            area_obj = Genareser.objects.using('readonly').filter(oid=ing.genareser).first()
            if area_obj:
               area_nombre = area_obj.gasnombre

        results.append({
            'ingreso_id': ing.oid,
            'paciente_id': pac.oid,
            'documento': pac.pacnumdoc,
            'nombre': f"{pac.pacprinom or ''} {pac.pacsegnom or ''} {pac.pacpriape or ''} {pac.pacsegape or ''}".strip(),
            'edad': calculate_age(pac.gpafecnac) if pac.gpafecnac else "N/A",
            'cama': cama_nombre,
            'area': area_nombre,
            'fecha_ingreso': ing.ainfecing.strftime('%d/%m/%Y %H:%M') if ing.ainfecing else "N/A"
        })
        
    return JsonResponse({'results': results})

@login_required
def api_paciente_data(request, ingreso_id):
    """
    Retorna el detalle completo de un paciente para el auto-llenado.
    """
    try:
        ingreso = get_object_or_404(Adningreso.objects.using('readonly'), oid=ingreso_id)
        pac = ingreso.genpacien
        
        if not pac:
            return JsonResponse({'error': 'Paciente no encontrado'}, status=404)
            
        # Obtener cama y servicio
        cama_obj = Hpndefcam.objects.using('readonly').filter(oid=ingreso.hpndefcam).first()
        cama_nombre = cama_obj.hcacodigo if cama_obj else "S/C"
        servicio_nombre = "HOSPITALIZACION"
        
        if ingreso.genareser:
            area_obj = Genareser.objects.using('readonly').filter(oid=ingreso.genareser).first()
            if area_obj:
                servicio_nombre = area_obj.gasnombre

        # Mapeo de campos para el frontend
        data = {
            'nombre_paciente': f"{pac.pacprinom or ''} {pac.pacsegnom or ''} {pac.pacpriape or ''} {pac.pacsegape or ''}".strip(),
            'identificacion': pac.pacnumdoc,
            'tipo_documento': pac.pactipdoc,
            'sexo': 'M' if pac.gpasexpac == 1 else 'F' if pac.gpasexpac == 2 else 'O',
            'edad': calculate_age(pac.gpafecnac) if pac.gpafecnac else "",
            'fecha_nacimiento': pac.gpafecnac.strftime('%Y-%m-%d') if pac.gpafecnac else "",
            'cama': cama_nombre,
            'servicio': servicio_nombre,
            'ingreso_id': ingreso.oid,
            'folio': ingreso.oid # Para fines de demostración
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def registro_firma_staff(request):
    """
    Vista para que el personal médico registre su firma oficial.
    """
    from .models import FirmaFuncionario
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            firma_base64 = data.get('firma_base64')
            
            if not firma_base64:
                return JsonResponse({'status': 'error', 'message': 'No se recibió la firma'}, status=400)
                
            firma_obj, created = FirmaFuncionario.objects.update_or_create(
                user=request.user,
                defaults={'firma_data': firma_base64, 'activo': True}
            )
            return JsonResponse({'status': 'ok', 'message': 'Firma oficial registrada con éxito'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    # GET: Mostrar la página de registro
    firma_actual = FirmaFuncionario.objects.filter(user=request.user, activo=True).first()
    return render(request, 'consentimientos/registro_firma.html', {
        'firma_actual': firma_actual
    })

@login_required
def api_historial_firmas(request):
    """
    Retorna el historial de firmas del paciente seleccionado.
    """
    ingreso_id = request.GET.get('ingreso_id')
    historia = request.GET.get('historia')
    
    query = Q()
    if ingreso_id:
        query &= Q(ingreso_id=ingreso_id)
    if historia:
        query &= Q(historia_clinica=historia)
        
    if not query:
        return JsonResponse({'results': []})
        
    firmas = FirmaBiometrica.objects.filter(query).select_related('documento').order_by('-timestamp')
    
    results = []
    for f in firmas:
        results.append({
            'pk': f.pk,
            'titulo': f.documento.titulo,
            'fecha': f.timestamp.strftime('%d/%m/%Y %H:%M'),
            'folio': f.folio,
            'descargar_url': f"/consentimientos-v2/firma/{f.pk}/descargar/"
        })
        
    return JsonResponse({'results': results})
