import json

from django.http import FileResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services.certificate_service import generate_certificate
from .services.contract_repository import get_grouped_contracts_by_cedula


def index(request):
    return render(request, "certificados/index.html")


@require_GET
def health(_request):
    return JsonResponse({"ok": True})


@require_GET
def empleado_por_cedula(_request, cedula):
    try:
        grouped = get_grouped_contracts_by_cedula(cedula)
        return JsonResponse(grouped)
    except Exception as error:
        return JsonResponse({"message": str(error)}, status=404)


@csrf_exempt
@require_POST
def generar_certificado(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest(json.dumps({"message": "JSON inválido."}), content_type="application/json")

    cedula = payload.get("cedula")
    genero = payload.get("genero")

    if not cedula:
        return JsonResponse({"message": "La cédula es obligatoria."}, status=400)

    try:
        data = get_grouped_contracts_by_cedula(cedula)
        file_buffer, filename = generate_certificate(data=data, genero=genero)
        response = FileResponse(
            file_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return response
    except Exception as error:
        return JsonResponse({"message": str(error)}, status=400)
