from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages
from django.conf import settings
import json
import base64
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from datetime import date

# Importaciones de modelos consolidados
from unificador_v1.models.meows import (
    PacienteMEOWS as Paciente, 
    FormularioMEOWS as Formulario, 
    ParametroMEOWS_Def as Parametro, 
    MedicionMEOWS as Medicion, 
    MedicionValorMEOWS as MedicionValor, 
    RangoParametroMEOWS as RangoParametro, 
    Hpnestanc,
    FirmaPacienteMEOWS as FirmaPaciente
)
from unificador_v1.models.base import AtencionParto

# Nota: El servicio de cálculo debe ser actualizado o movido también.
# Por ahora asumimos que sigue en meows.services hasta que lo movamos.
from unificador_v1.services.meows import calcular_score_desde_bd, calcular_meows

def abrir_meows_desde_atencion(request, doc=None):
    atencion_id = (request.GET.get("atencion") or "").strip()
    documento = (doc or request.GET.get("doc") or "").strip()
    if not documento:
        messages.warning(request, "Debe seleccionar un paciente desde Sala de Partos para ingresar a este módulo.")
        return redirect("/atencion/sala-de-partos/")

    paciente = Paciente.objects.filter(numero_documento=documento).first()
    if not paciente:
        paciente = Paciente.objects.create(numero_documento=documento, nombres="N/A", apellidos="N/A", sexo="F")

    query = f"?doc={documento}"
    if atencion_id: query += f"&atencion={atencion_id}"
    return redirect(f"/unificador/meows/nuevo/{paciente.id}/{query}")

def crear_medicion_meows(request, paciente_id):
    atencion_id = request.GET.get("atencion")
    paciente = get_object_or_404(Paciente, id=paciente_id)
    formulario, _ = Formulario.objects.get_or_create(
        codigo="MEOWS",
        defaults={'nombre': 'Sistema de Alerta Temprana Obstétrico', 'version': '1.0', 'activo': True}
    )
    parametros = Parametro.objects.filter(activo=True).order_by("orden")

    if request.method == "POST":
        atencion_id = (request.POST.get("atencion") or request.GET.get("atencion") or "").strip()
        nuevo_numero_doc = request.POST.get('numero_documento', '').strip()
        if not nuevo_numero_doc:
            messages.error(request, 'El número de documento es requerido.')
            return render(request, "unificador_v1/meows/formulario.html", {"paciente": paciente, "parametros": parametros})
        
        nombre_completo = request.POST.get('nombre_completo', '').strip()
        if nombre_completo:
            partes = nombre_completo.split(maxsplit=1)
            nombres_nuevo = partes[0] if len(partes) >= 1 else ''
            apellidos_nuevo = partes[1] if len(partes) >= 2 else ''
        else:
            nombres_nuevo = request.POST.get('nombres', '')
            apellidos_nuevo = request.POST.get('apellidos', '')
        
        paciente_existente = Paciente.objects.filter(numero_documento=nuevo_numero_doc).first()
        if paciente_existente:
            paciente = paciente_existente
            if nombre_completo:
                paciente.nombres = nombres_nuevo
                paciente.apellidos = apellidos_nuevo
        else:
            paciente = Paciente.objects.create(numero_documento=nuevo_numero_doc, nombres=nombres_nuevo or 'N/A', apellidos=apellidos_nuevo or 'N/A', sexo='F')
        
        paciente.aseguradora = request.POST.get('aseguradora', '')
        paciente.cama = request.POST.get('cama', '')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        paciente.fecha_nacimiento = fecha_nacimiento if fecha_nacimiento else None
        fecha_ingreso = request.POST.get('fecha_ingreso')
        paciente.fecha_ingreso = fecha_ingreso if fecha_ingreso else None
        paciente.responsable = request.POST.get('responsable', '')
        
        try:
            paciente.save()
        except IntegrityError:
            messages.error(request, 'Error al guardar los datos del paciente. El número de documento ya existe.')
            return render(request, "unificador_v1/meows/formulario.html", {"paciente": paciente, "parametros": parametros})
        
        atencion = None
        if atencion_id:
            try: atencion = AtencionParto.objects.get(id=atencion_id)
            except Exception: atencion = None

        medicion = Medicion.objects.create(paciente=paciente, formulario=formulario, atencion=atencion)
        valores_dict = {}
        for parametro in parametros:
            valor = request.POST.get(parametro.codigo)
            if valor:
                MedicionValor.objects.create(medicion=medicion, parametro=parametro, valor=valor)
                valores_dict[parametro.codigo] = valor

        resultados_meows = calcular_meows(valores_dict)
        medicion.meows_total = resultados_meows["meows_total"]
        medicion.meows_riesgo = resultados_meows["meows_riesgo"]
        medicion.meows_mensaje = resultados_meows["meows_mensaje"]
        medicion.save(update_fields=["meows_total", "meows_riesgo", "meows_mensaje"])

        messages.success(request, 'Registro MEOWS guardado exitosamente.')
        query_string = f"?doc={paciente.numero_documento}"
        if atencion_id: query_string += f"&atencion={atencion_id}"
        return redirect(f"/unificador/meows/nuevo/{paciente.id}/{query_string}")

    return render(request, "unificador_v1/meows/formulario.html", {
        "paciente": paciente,
        "parametros": parametros,
        "atencion_id": request.GET.get("atencion"),
        "documento": request.GET.get("doc"),
    })

def ver_meows(request, medicion_id):
    medicion = get_object_or_404(Medicion, id=medicion_id)
    return render(request, "unificador_v1/meows/resultado.html", {
        "medicion": medicion,
        "valores": medicion.valores.select_related("parametro").order_by("parametro__orden")
    })

@require_http_methods(["GET"])
def api_rangos_meows(request):
    rangos_dict = {}
    parametros = Parametro.objects.filter(activo=True)
    for parametro in parametros:
        rangos = RangoParametro.objects.filter(parametro=parametro, activo=True).order_by('orden', 'valor_min')
        rangos_dict[parametro.codigo] = [{'min': float(r.valor_min), 'max': float(r.valor_max), 'score': r.score} for r in rangos]
    return JsonResponse(rangos_dict, json_dumps_params={'ensure_ascii': False})

@require_http_methods(["POST"])
def api_calcular_score(request):
    try:
        data = json.loads(request.body)
        codigo_parametro = data.get('parametro')
        valor = float(data.get('valor'))
        score = calcular_score_desde_bd(codigo_parametro, valor)
        return JsonResponse({'success': True, 'score': score, 'parametro': codigo_parametro, 'valor': valor})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def api_buscar_paciente(request):
    numero_documento = request.GET.get('documento', '').strip()
    if not numero_documento: return JsonResponse({'success': False, 'error': 'Número de documento requerido'}, status=400)
    
    documento_limpio = numero_documento.lstrip('0') or '0'
    IDs_busqueda = [numero_documento]
    if documento_limpio != numero_documento: IDs_busqueda.append(documento_limpio)
    
    huella_reciente = FirmaPaciente.objects.filter(paciente_id__in=IDs_busqueda).exclude(imagen_huella=None).exclude(imagen_huella='').order_by('-fecha').first()
    firma_reciente = FirmaPaciente.objects.filter(paciente_id__in=IDs_busqueda).exclude(imagen_firma=None).exclude(imagen_firma='').order_by('-fecha').first()
    
    import os
    huella_url = huella_reciente.imagen_huella.url if huella_reciente and huella_reciente.imagen_huella and os.path.exists(huella_reciente.imagen_huella.path) else None
    firma_url = firma_reciente.imagen_firma.url if firma_reciente and firma_reciente.imagen_firma and os.path.exists(firma_reciente.imagen_firma.path) else None
    biometria_data = {'imagen_huella': huella_url, 'imagen_firma': firma_url}

    try:
        paciente = Paciente.objects.get(numero_documento=numero_documento)
        return JsonResponse({
            'success': True, 'origen': 'local',
            'paciente': {
                'id': paciente.id, 'nombre_completo': f"{paciente.nombres} {paciente.apellidos}".strip(),
                'numero_documento': paciente.numero_documento, 'edad': paciente.edad,
                'aseguradora': paciente.aseguradora, 'cama': paciente.cama,
                'fecha_ingreso': paciente.fecha_ingreso.strftime('%Y-%m-%d') if paciente.fecha_ingreso else '',
                'responsable': paciente.responsable, 'nombres': paciente.nombres, 'apellidos': paciente.apellidos,
                'sexo': paciente.sexo, 'fecha_nacimiento': paciente.fecha_nacimiento.strftime('%Y-%m-%d') if paciente.fecha_nacimiento else '',
                'biometria': biometria_data,
            }
        }, json_dumps_params={'ensure_ascii': False})
    except Paciente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Paciente no encontrado'}, status=404)

@require_http_methods(["GET"])
def api_pacientes_activos(request):
    return JsonResponse({'success': True, 'count': 0, 'pacientes': [], 'message': 'Endpoint migrado. Use consulta unificada.'})

def historial_meows_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    mediciones = Medicion.objects.filter(paciente=paciente).prefetch_related('valores__parametro').order_by("-fecha_hora")
    mediciones_data = []
    for m in mediciones:
        v_dict = {v.parametro.codigo: {'valor': v.valor, 'puntaje': v.puntaje, 'nombre': v.parametro.nombre, 'unidad': v.parametro.unidad} for v in m.valores.all()}
        mediciones_data.append({'medicion': m, 'valores': v_dict})
    return render(request, "unificador_v1/meows/historial.html", {"paciente": paciente, "mediciones_data": mediciones_data})

def generar_pdf_meows_paciente(request, paciente_id):
    from unificador_v1.generador_pdf_meows import generar_pdf_meows
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    mediciones = list(Medicion.objects.filter(paciente=paciente).order_by("fecha_hora"))
    if not mediciones:
        messages.error(request, 'El paciente no tiene mediciones registradas.')
        return redirect('historial_meows', paciente_id=paciente_id)
    return generar_pdf_meows(paciente, mediciones)

@csrf_exempt
def guardar_huella(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else {}
            paciente_id = data.get("paciente_id")
            if not paciente_id: return JsonResponse({"status": "error", "message": "paciente_id requerido"}, status=400)
            registro, _ = FirmaPaciente.objects.update_or_create(
                paciente_id=str(paciente_id),
                defaults={'formulario_id': data.get("formulario_id"), 'template_huella': data.get("template") or "", 'usuario': str(data.get("usuario", "Sistema"))}
            )
            img_b64 = data.get("imagen_huella") or data.get("imagen")
            if img_b64:
                imgstr = img_b64.split(';base64,')[1] if ';base64,' in str(img_b64) else str(img_b64)
                registro.imagen_huella.save(f"huella_{paciente_id}.png", ContentFile(base64.b64decode(imgstr)), save=True)
            frm_b64 = data.get("firma")
            if frm_b64:
                imgstr = frm_b64.split(';base64,')[1] if ';base64,' in str(frm_b64) else str(frm_b64)
                registro.imagen_firma.save(f"firma_{paciente_id}.png", ContentFile(base64.b64decode(imgstr)), save=True)
            return JsonResponse({"status": "ok", "id": registro.id})
        except Exception as e: return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

def ultima_huella(request, paciente_id):
    huella = FirmaPaciente.objects.filter(paciente_id=paciente_id).exclude(imagen_huella='').order_by('-fecha').first()
    firma = FirmaPaciente.objects.filter(paciente_id=paciente_id).exclude(imagen_firma='').order_by('-fecha').first()
    if huella or firma:
        ref = huella or firma
        return JsonResponse({
            "status": "ok", "paciente_id": paciente_id, "template": huella.template_huella if huella else "",
            "imagen_huella": huella.imagen_huella.url if huella else None,
            "imagen_firma": firma.imagen_firma.url if firma else None,
            "fecha": ref.fecha.strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse({"status": "error", "message": "No encontrado"}, status=404)
