from io import BytesIO
import os
import re
import time
import unicodedata
from pathlib import Path

from docxtpl import DocxTemplate

from .date_utils import get_spanish_expedition_date

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DOCX_DIR = BASE_DIR / "templates_docx"


def score_corruption(text):
    return len(re.findall(r"Ã|Â|â|�|[\u0080-\u009f]", text))


def repair_common_mojibake(text):
    replacements = {
        "Ã¡": "á",
        "Ã©": "é",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã": "Á",
        "Ã‰": "É",
        "Ã": "Í",
        "Ã“": "Ó",
        "Ãš": "Ú",
        "Ã±": "ñ",
        "Ã‘": "Ñ",
        "Ã¼": "ü",
        "Ãœ": "Ü",
        "â€“": "–",
        "â€”": "—",
        "â€œ": "“",
        "â€": "”",
        "â€˜": "‘",
        "â€™": "’",
        "Â": "",
        "Ã?O": "ÑO",
        "Ã?o": "ño",
        "Ã?N": "ÓN",
        "Ã?n": "ón",
    }
    output = text
    for source, target in replacements.items():
        output = output.replace(source, target)
    return output


def sanitize_text(value):
    text = str(value or "")
    if not text:
        return text
    if re.search(r"Ã|Â|â|[\u0080-\u009f]", text):
        decoded = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
        if score_corruption(decoded) < score_corruption(text):
            text = decoded
    text = repair_common_mojibake(text)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\uFFFD", "")
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text).strip()


def sanitize_template_data(value):
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_template_data(item) for item in value]
    if isinstance(value, dict):
        return {k: sanitize_template_data(v) for k, v in value.items()}
    return value


def template_path_by_gender(genero):
    normalized = str(genero or "").lower().strip()
    if normalized == "femenino":
        return TEMPLATES_DOCX_DIR / "plantilla_femenina.docx"
    return TEMPLATES_DOCX_DIR / "plantilla_masculina.docx"


def generate_certificate(data, genero):
    clean_data = sanitize_template_data(data)
    template_path = template_path_by_gender(genero)
    if not template_path.exists():
        raise ValueError(f"No existe la plantilla: {template_path}")

    doc = DocxTemplate(str(template_path))
    fecha = get_spanish_expedition_date()
    context = {
        "nombre": clean_data.get("nombre"),
        "cedula": clean_data.get("cedula"),
        "cargo": clean_data.get("cargo"),
        "contratos": clean_data.get("contratos"),
        "objeto_ctto": clean_data.get("cargo"),
        "dia": fecha["dia"],
        "mes": fecha["mes"],
        "anio": fecha["anio"],
        "fecha_expedicion_texto": fecha["fecha_texto"],
    }

    try:
        doc.render(context)
    except Exception as error:
        raise ValueError(
            f"Error al renderizar la plantilla. Verifica etiquetas y bloque de contratos. Detalle: {error}"
        ) from error

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    filename = f"certificado_{clean_data.get('cedula')}_{int(time.time() * 1000)}.docx"
    return output, filename
