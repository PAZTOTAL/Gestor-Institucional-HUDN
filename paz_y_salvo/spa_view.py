"""
Sirve la SPA React de Paz y Salvo desde el build generado por Vite.
Si el build no existe, muestra instrucciones para compilarlo.
"""
import os
from pathlib import Path
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required


_BUILD_DIR = Path(__file__).resolve().parent / 'static' / 'paz_y_salvo'
_INDEX_HTML = _BUILD_DIR / 'index.html'


@login_required
def paz_y_salvo_spa(request):
    if _INDEX_HTML.exists():
        html = _INDEX_HTML.read_text(encoding='utf-8')
        return HttpResponse(html, content_type='text/html; charset=utf-8')

    # Build no compilado aún — mostrar instrucciones
    return HttpResponse(
        """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Paz y Salvo — HUDN</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f4f8; display: flex;
           align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
    .card { background: white; border-radius: 14px; padding: 40px 48px; max-width: 560px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.09); text-align: center; }
    h1 { color: #0369a1; margin-bottom: 8px; }
    p { color: #475569; line-height: 1.7; }
    code { background: #f1f5f9; border-radius: 6px; padding: 12px 16px; display: block;
           font-size: 14px; text-align: left; margin: 12px 0; color: #0f172a; }
    a { color: #0369a1; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Sistema de Paz y Salvos</h1>
    <p>El frontend aún no ha sido compilado.<br>
    Ejecuta los siguientes comandos en la terminal:</p>
    <code>cd PazYSalvo/HospitalAppZ<br>npm install<br>npm run build</code>
    <p>O para desarrollo, inicia el servidor React:<br>
    <code>npm run dev</code>
    y accede a <a href="http://localhost:5173" target="_blank">http://localhost:5173</a></p>
  </div>
</body>
</html>""",
        content_type='text/html; charset=utf-8',
        status=503,
    )
