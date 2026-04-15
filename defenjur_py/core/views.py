"""Vistas a nivel de proyecto (páginas que no pertenecen solo a la app legal)."""

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def favicon(request):
    """Evita 404: los navegadores piden /favicon.ico por defecto."""
    path = Path(settings.BASE_DIR) / 'static' / 'favicon.svg'
    if not path.is_file():
        return HttpResponseNotFound()
    return FileResponse(path.open('rb'), content_type='image/svg+xml')


def mantenimiento(request):
    """Equivalente a defenjur-front/index_mensaje_mantenimiento_actualizacion.php."""
    return render(
        request,
        'mantenimiento.html',
        {'support_email': getattr(settings, 'DEFENJUR_SUPPORT_EMAIL', 'soporte@defenjur.example')},
    )
