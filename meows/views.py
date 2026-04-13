from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.decorators import valida_acceso
from django.conf import settings
from datetime import datetime
from meows.models import Paciente, Formulario, Parametro, Medicion, MedicionValor, RangoParametro
from meows.services.meows import calcular_score_desde_bd
from meows.services.paciente_service import obtener_info_ingreso_activo, buscar_pacientes_activos_filtro
# Importación diferida del generador PDF para evitar errores de WeasyPrint al iniciar
# from meows.generador_pdf_meows import generar_pdf_meows


@login_required
@valida_acceso('meows')
def crear_medicion_meows(request, paciente_id):
    """
    Vista para crear una nueva medición MEOWS para un paciente.
    Si paciente_id=0, muestra formulario vacío para nuevo paciente.
    """
    # Si paciente_id es 0, crear un paciente temporal para el formulario
    if paciente_id == 0:
        paciente = None
    else:
        paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener o crear formulario MEOWS
    formulario, _ = Formulario.objects.get_or_create(
        codigo="MEOWS",
        defaults={
            'nombre': 'Sistema de Alerta Temprana Obstétrico',
            'version': '1.0',
            'activo': True
        }
    )
    
    parametros = Parametro.objects.filter(activo=True).order_by("orden")

    if request.method == "POST":
        # Obtener el número de documento del formulario
        nuevo_numero_doc = request.POST.get('numero_documento', '').strip()
        if not nuevo_numero_doc:
            messages.error(request, 'El número de documento es requerido.')
            return render(request, "meows/formulario.html", {
                "paciente": paciente,
                "parametros": parametros
            })
        
        # Separar nombre completo en nombres y apellidos
        nombre_completo = request.POST.get('nombre_completo', '').strip()
        if nombre_completo:
            partes = nombre_completo.split(maxsplit=1)
            nombres_nuevo = partes[0] if len(partes) >= 1 else ''
            apellidos_nuevo = partes[1] if len(partes) >= 2 else ''
        else:
            nombres_nuevo = request.POST.get('nombres', '')
            apellidos_nuevo = request.POST.get('apellidos', '')
        
        # Buscar si ya existe un paciente con este número de documento
        paciente_existente = Paciente.objects.filter(numero_documento=nuevo_numero_doc).first()
        
        if paciente_existente:
            # Si existe un paciente con este documento, usar ese paciente (NO reemplazar el de la URL)
            paciente = paciente_existente
            # Actualizar solo los campos que vienen del formulario
            if nombre_completo:
                paciente.nombres = nombres_nuevo
                paciente.apellidos = apellidos_nuevo
        else:
            # Si NO existe, crear un nuevo paciente (NO actualizar el paciente de la URL)
            # NOTA: tipo_documento y fecha_nacimiento son propiedades de solo lectura
            # que se obtienen automáticamente de Genpacien
            paciente = Paciente.objects.create(
                numero_documento=nuevo_numero_doc,
                nombres=nombres_nuevo or 'N/A',
                apellidos=apellidos_nuevo or 'N/A',
                sexo='F'  # Valor por defecto
            )
        
        # Actualizar campos opcionales (tanto si es existente como si es nuevo)


        paciente.aseguradora = request.POST.get('aseguradora', '')
        paciente.cama = request.POST.get('cama', '')
        fecha_ingreso = request.POST.get('fecha_ingreso')
        paciente.fecha_ingreso = fecha_ingreso if fecha_ingreso else None
        paciente.responsable = request.POST.get('responsable', '')
        
        # LOGICA DE ACTUALIZACIÓN AUTOMÁTICA (BED/INSURER)
        # Si el paciente se está creando o actualizando, intentar traer datos frescos de cama/aseguradora si está activo
        try:
            info_activa = obtener_info_ingreso_activo(paciente.numero_documento)
            if info_activa:
                if info_activa['cama']:
                    paciente.cama = info_activa['cama']
                if info_activa['aseguradora']:
                    paciente.aseguradora = info_activa['aseguradora']
                if info_activa['fecha_ingreso']:
                    paciente.fecha_ingreso = info_activa['fecha_ingreso']
        except Exception as e:
            print(f"Error actualizando datos activos: {e}")
        
        try:
            paciente.save()
        except IntegrityError as e:
            messages.error(request, 'Error al guardar los datos del paciente. El número de documento ya existe.')
            return render(request, "meows/formulario.html", {
                "paciente": paciente,
                "parametros": parametros
            })
        
        # Crear la medición
        medicion = Medicion.objects.create(
            paciente=paciente,
            formulario=formulario
        )

        # Crear los valores de medición
        valores_dict = {}
        for parametro in parametros:
            valor = request.POST.get(parametro.codigo)
            if valor:
                MedicionValor.objects.create(
                    medicion=medicion,
                    parametro=parametro,
                    valor=valor
                )
                # Guardar para cálculo manual
                valores_dict[parametro.codigo] = valor

        # Calcular MEOWS manualmente (por si el signal no se ejecuta correctamente)
        if valores_dict:
            from meows.services.meows import calcular_meows
            resultado = calcular_meows(valores_dict)
            
            # Actualizar la medición con los resultados
            medicion.meows_total = resultado['meows_total']
            medicion.meows_riesgo = resultado['meows_riesgo']
            medicion.meows_mensaje = resultado['meows_mensaje']
            medicion.save()
            
            # Actualizar puntajes individuales
            for mv in medicion.valores.all():
                if mv.parametro.codigo in resultado['puntajes']:
                    mv.puntaje = resultado['puntajes'][mv.parametro.codigo]
                    mv.save()

        # Redirigir para mostrar resultado
        return redirect("ver_meows", medicion_id=medicion.id)

    return render(request, "meows/formulario.html", {
        "paciente": paciente,
        "parametros": parametros
    })


@login_required
@valida_acceso('meows')
def ver_meows(request, medicion_id):
    """
    Vista para mostrar el resultado de una medición MEOWS.
    """
    medicion = get_object_or_404(Medicion, id=medicion_id)

    return render(request, "meows/resultado.html", {
        "medicion": medicion,
        "valores": medicion.valores.select_related("parametro").order_by("parametro__orden")
    })


@require_http_methods(["GET"])
def api_rangos_meows(request):
    """
    API endpoint para obtener los rangos MEOWS desde la base de datos.
    Retorna JSON con los rangos organizados por código de parámetro.
    """
    rangos_dict = {}
    
    # Obtener todos los parámetros activos
    parametros = Parametro.objects.filter(activo=True)
    
    for parametro in parametros:
        # Obtener rangos activos del parámetro, ordenados
        rangos = RangoParametro.objects.filter(
            parametro=parametro,
            activo=True
        ).order_by('orden', 'valor_min')
        
        rangos_dict[parametro.codigo] = [
            {
                'min': float(rango.valor_min),
                'max': float(rango.valor_max),
                'score': rango.score
            }
            for rango in rangos
        ]
    
    return JsonResponse(rangos_dict, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["POST"])
def api_calcular_score(request):
    """
    API endpoint para calcular el score de un valor específico.
    """
    import json
    
    try:
        data = json.loads(request.body)
        codigo_parametro = data.get('parametro')
        valor = float(data.get('valor'))
        
        # Calcular score desde base de datos
        score = calcular_score_desde_bd(codigo_parametro, valor)
        
        return JsonResponse({
            'success': True,
            'score': score,
            'parametro': codigo_parametro,
            'valor': valor
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def api_buscar_pacientes_activos(request):
    """
    API para buscar listado de pacientes ACTIVOS (hospitalizados).
    """
    query = request.GET.get('q', '').strip()
    # Si query vacio, trae por defecto los recientes
    
    resultados = buscar_pacientes_activos_filtro(query)
    
    return JsonResponse({
        'success': True,
        'pacientes': resultados
    }, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def api_buscar_paciente(request):
    """
    API endpoint para buscar un paciente por número de documento.
    Retorna los datos del paciente en formato JSON.
    Si no existe localmente, busca en la base de datos externa (Genpacien).
    """
    numero_documento = request.GET.get('documento', '').strip()
    
    if not numero_documento:
        return JsonResponse({
            'success': False,
            'error': 'Número de documento requerido'
        }, status=400)
    
    try:
        # 1. Buscar localmente
        paciente = Paciente.objects.get(numero_documento=numero_documento)
        
        # SIEMPRE intentar refrescar datos de actividad (Cama/Aseguradora) si existe
        info_activa = obtener_info_ingreso_activo(numero_documento)
        if info_activa:
            if info_activa['cama'] and paciente.cama != info_activa['cama']:
                paciente.cama = info_activa['cama']
            if info_activa['aseguradora'] and paciente.aseguradora != info_activa['aseguradora']:
                paciente.aseguradora = info_activa['aseguradora']
            # Opcional: Actualizar fecha ingreso si es diferente?
            # Guardamos para persistir el dato fresco
            paciente.save()

        return JsonResponse({
            'success': True,
            'origen': 'local',
            'paciente': {
                'id': paciente.id,
                'nombre_completo': f"{paciente.nombres} {paciente.apellidos}".strip(),
                'numero_documento': paciente.numero_documento,
                'edad': paciente.edad if paciente.edad else None,
                'aseguradora': paciente.aseguradora if paciente.aseguradora else '',
                'cama': paciente.cama if paciente.cama else '',
                'fecha_ingreso': paciente.fecha_ingreso.strftime('%Y-%m-%d') if paciente.fecha_ingreso else '',
                'responsable': paciente.responsable if paciente.responsable else '',
                'tipo_documento': paciente.tipo_documento,
                'nombres': paciente.nombres,
                'apellidos': paciente.apellidos,
                'sexo': paciente.sexo,
                'fecha_nacimiento': paciente.fecha_nacimiento.strftime('%Y-%m-%d') if paciente.fecha_nacimiento else '',
            }
        }, json_dumps_params={'ensure_ascii': False})
        
    except Paciente.DoesNotExist:
        # 2a. PRIORIDAD: Buscar en servicio de activos (Mejorado)
        # Esto asegura que si el paciente está activo, traigamos sus datos frescos (Cama, Aseguradora)
        info_activa = obtener_info_ingreso_activo(numero_documento)
        
        if info_activa:
            return JsonResponse({
                'success': True,
                'origen': 'externo_activo',
                'paciente': {
                    'id': None, # No guardado aun
                    'nombre_completo': info_activa['paciente_nombre'],
                    'numero_documento': numero_documento,
                    'edad': None, # Se calculará al guardar o front
                    'aseguradora': info_activa['aseguradora'] or '',
                    'cama': info_activa['cama'] or '',
                    'fecha_ingreso': info_activa['fecha_ingreso'].strftime('%Y-%m-%d') if info_activa['fecha_ingreso'] else '',
                    'responsable': '',
                    'tipo_documento': 'CC', 
                    'nombres': info_activa.get('nombres', ''),
                    'apellidos': info_activa.get('apellidos', ''),
                    'sexo': '',
                    'fecha_nacimiento': info_activa['fecha_nacimiento'].strftime('%Y-%m-%d') if info_activa.get('fecha_nacimiento') else '',
                    'es_activo': True
                }
            }, json_dumps_params={'ensure_ascii': False})

        # 2. Si no es activo o falla, intentar búsqueda standard en externa (Genpacien)
        try:
            paciente_temp = Paciente(numero_documento=numero_documento)
            paciente_temp.poblar_datos_basicos()
            
            if paciente_temp.nombres: # Si encontró datos
                return JsonResponse({
                    'success': True,
                    'origen': 'externo',
                    'paciente': {
                        'id': None, # No guardado aun
                        'nombre_completo': f"{paciente_temp.nombres} {paciente_temp.apellidos}".strip(),
                        'numero_documento': paciente_temp.numero_documento,
                        'edad': paciente_temp.edad,
                        'aseguradora': paciente_temp.aseguradora,
                        'cama': paciente_temp.cama,
                        'fecha_ingreso': '',
                        'responsable': paciente_temp.responsable,
                        'tipo_documento': paciente_temp.tipo_documento,
                        'nombres': paciente_temp.nombres,
                        'apellidos': paciente_temp.apellidos,
                        'sexo': paciente_temp.sexo,
                        'fecha_nacimiento': paciente_temp.fecha_nacimiento.strftime('%Y-%m-%d') if paciente_temp.fecha_nacimiento else '',
                    }
                }, json_dumps_params={'ensure_ascii': False})
        except Exception:
            # Ignorar errores de conexión externa y continuar con fallback
            pass



        # 3. Fallback: Intentar búsqueda local más flexible (sin ceros iniciales, etc.)
        try:
            documento_limpio = numero_documento.lstrip('0') or '0'
            # Evitar buscar si es igual al original para no repetir
            if documento_limpio != numero_documento:
                paciente = Paciente.objects.filter(numero_documento__endswith=documento_limpio).first()
                
                if paciente:
                    return JsonResponse({
                        'success': True,
                        'origen': 'local_fuzzy',
                        'paciente': {
                            'id': paciente.id,
                            'nombre_completo': f"{paciente.nombres} {paciente.apellidos}".strip(),
                            'numero_documento': paciente.numero_documento,
                            'edad': paciente.edad if paciente.edad else None,
                            'aseguradora': paciente.aseguradora if paciente.aseguradora else '',
                            'cama': paciente.cama if paciente.cama else '',
                            'fecha_ingreso': paciente.fecha_ingreso.strftime('%Y-%m-%d') if paciente.fecha_ingreso else '',
                            'responsable': paciente.responsable if paciente.responsable else '',
                            'tipo_documento': paciente.tipo_documento,
                            'nombres': paciente.nombres,
                            'apellidos': paciente.apellidos,
                            'sexo': paciente.sexo,
                            'fecha_nacimiento': paciente.fecha_nacimiento.strftime('%Y-%m-%d') if paciente.fecha_nacimiento else '',
                        }
                    }, json_dumps_params={'ensure_ascii': False})
        except Exception:
            pass
        
        return JsonResponse({
            'success': False,
            'error': 'Paciente no encontrado'
        }, status=404)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc() if settings.DEBUG else None
        }, status=500)


@login_required
@valida_acceso('meows')
def historial_meows_paciente(request, paciente_id):
    """
    Vista para mostrar el historial de mediciones MEOWS de un paciente.
    Muestra una línea de tiempo clínica con todas las mediciones ordenadas por fecha.
    Solo muestra las mediciones del paciente específico identificado por paciente_id.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener SOLO las mediciones del paciente específico ordenadas por fecha (más reciente primero)
    # Usamos paciente=paciente para asegurar que solo se obtengan las mediciones de este paciente
    mediciones = Medicion.objects.filter(
        paciente=paciente
    ).select_related('formulario').prefetch_related(
        'valores__parametro'
    ).order_by("-fecha_hora")
    
    # Preparar datos para el template
    mediciones_data = []
    for medicion in mediciones:
        valores_dict = {}
        for valor_obj in medicion.valores.select_related('parametro').all():
            valores_dict[valor_obj.parametro.codigo] = {
                'valor': valor_obj.valor,
                'puntaje': valor_obj.puntaje,
                'nombre': valor_obj.parametro.nombre,
                'unidad': valor_obj.parametro.unidad
            }
        
        mediciones_data.append({
            'medicion': medicion,
            'valores': valores_dict
        })
    
    return render(request, "meows/historial.html", {
        "paciente": paciente,
        "mediciones_data": mediciones_data
    })


@login_required
@valida_acceso('meows')
def generar_pdf_meows_paciente(request, paciente_id):
    """
    Vista para generar el PDF MEOWS de un paciente con todas sus mediciones.
    Replica exactamente el formato físico del documento.
    """
    # Importación diferida para evitar errores al iniciar el servidor
    from meows.generador_pdf_meows import generar_pdf_meows
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener todas las mediciones del paciente ordenadas por fecha (más antiguas primero)
    mediciones = Medicion.objects.filter(
        paciente=paciente
    ).select_related('formulario').prefetch_related(
        'valores__parametro'
    ).order_by("fecha_hora")
    
    if not mediciones.exists():
        messages.error(request, 'El paciente no tiene mediciones registradas para generar el PDF.')
        return redirect('historial_meows', paciente_id=paciente_id)
    
    # Generar el PDF
    return generar_pdf_meows(paciente, mediciones)
