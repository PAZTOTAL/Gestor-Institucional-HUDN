"""
Genera el PDF FRRHU-030 usando Jinja2 + Playwright (Chromium headless).
Los archivos de plantilla e imágenes están en horas_extras/utils/.
"""
import base64
import os
from datetime import date

from jinja2 import Environment, FileSystemLoader

# Si está definido en .env, apunta Playwright a la ruta compartida
# (necesario cuando el servidor corre como servicio/SYSTEM)
_pw_path = os.getenv('PLAYWRIGHT_BROWSERS_PATH')
if _pw_path:
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = _pw_path

_HERE = os.path.dirname(os.path.abspath(__file__))
# Plantilla e imágenes dentro de horas_extras/utils/format/
TEMPLATE_DIR = os.path.join(_HERE, 'format')

TEMPLATE_FILE = 'FRRHU-030.html'

MESES_ES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


def _img_base64(filename: str) -> str:
    """Lee una imagen y la devuelve como data URI base64."""
    # Primero busca junto a la plantilla, luego en utils/
    for base in [TEMPLATE_DIR, _HERE]:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
            ext  = os.path.splitext(filename)[1].lower().lstrip('.')
            mime = 'image/svg+xml' if ext == 'svg' else f'image/{ext}'
            return f'data:{mime};base64,{data}'
    return ''


_POR_PAGINA = 16


def _chunk_empleados(empleados_data: list, page_size: int = _POR_PAGINA) -> list:
    """Divide la lista en páginas de `page_size` empleados con sus subtotales."""
    paginas = []
    for i in range(0, max(1, len(empleados_data)), page_size):
        chunk = empleados_data[i:i + page_size]
        paginas.append({
            'empleados':  chunk,
            'total_hon':  sum(int(e.get('hon') or 0) for e in chunk),
            'total_hdf':  sum(int(e.get('hdf') or 0) for e in chunk),
            'total_hnf':  sum(int(e.get('hnf') or 0) for e in chunk),
        })
    return paginas


def generar_pdf_html(area_nombre: str, year: int, month: int,
                     empleados_data: list,
                     tipo: str = None,
                     coordinador_nombre: str = '') -> bytes:
    """
    Renderiza FRRHU-030.html con Jinja2 y exporta a PDF con Playwright.

    empleados_data: lista de dicts con claves:
        documento, nombre, hon, hdf, hnf, observaciones
    tipo: 'temporal' | 'permanente' | None

    Si hay más de 16 empleados se generan varias páginas, cada una con
    su propio encabezado, listado (máx. 16) y sección de firmas.
    """
    paginas       = _chunk_empleados(empleados_data)
    total_paginas = len(paginas)

    env      = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template(TEMPLATE_FILE)
    html     = template.render(
        area_nombre        = area_nombre,
        mes_anio           = f'{MESES_ES[month]} {year}',
        fecha_expedicion   = date.today().strftime('%d/%m/%Y'),
        responsable        = coordinador_nombre,
        coordinador_nombre = coordinador_nombre,
        paginas            = paginas,
        total_paginas      = total_paginas,
        tipo               = tipo,
        logo_hospital      = _img_base64('logo_hospital.png'),
        logo_acreditacion  = _img_base64('logo_acreditacion.png'),
    )

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()
        page.set_content(html, wait_until='networkidle')
        pdf_bytes = page.pdf(
            format           = 'Letter',
            landscape        = True,
            print_background = True,
            margin           = {'top': '8mm', 'right': '10mm', 'bottom': '8mm', 'left': '10mm'},
        )
        browser.close()

    return pdf_bytes
