from django.shortcuts import render
from django.http import JsonResponse
import json
import logging
from django.http import HttpResponse

from .services.contract_repository import get_grouped_contracts_by_cedula
from .services.certificate_service import generate_certificate

logger = logging.getLogger(__name__)

def certificados_laborales_index(request):
    return render(request, "certificados_laborales/index.html")

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_consultar_contratos(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        cedula = data.get("cedula")
        if not cedula:
            return JsonResponse({"error": "La cédula es requerida."}, status=400)

        result = get_grouped_contracts_by_cedula(cedula)
        return JsonResponse(result)

    except ValueError as e:
        logger.warning(f"Error de validación al consultar cédula {cedula}: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.exception(f"Error interno al consultar cédula {cedula}: {str(e)}")
        return JsonResponse(
            {"error": "Error interno del servidor al procesar la solicitud."}, status=500
        )

@csrf_exempt
def api_generar_certificado(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
            cedula = payload.get("cedula")
            genero = payload.get("genero", "masculino")
        else:
            cedula = request.POST.get("cedula")
            genero = request.POST.get("genero", "masculino")
        
        if not cedula:
            return JsonResponse({"error": "Cédula requerida"}, status=400)

        data = get_grouped_contracts_by_cedula(cedula)
        output, filename = generate_certificate(data, genero)

        from django.http import HttpResponse
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    except ValueError as e:
        logger.warning(f"Error de validación al generar certificado: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.exception(f"Error interno al generar certificado: {str(e)}")
        return JsonResponse(
            {"error": "Error interno al generar el documento pdf/docx."}, status=500
        )
