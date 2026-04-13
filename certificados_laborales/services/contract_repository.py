import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from threading import Lock
from time import time

DB_SCHEMA = os.getenv("DB_SCHEMA", "dbo")
DB_METADATA_CACHE_TTL_MS = int(os.getenv("DB_METADATA_CACHE_TTL_MS", "300000"))
DB_MAX_CONTRACT_YEAR = int(os.getenv("DB_MAX_CONTRACT_YEAR", "2026"))

_cache_lock = Lock()
_metadata_cache = {"expires_at": 0, "tables": None}


def quote_identifier(value):
    return f"[{str(value).replace(']', ']]')}]"


def build_digits_only_sql(expression):
    return (
        f"REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
        f"CAST({expression} AS NVARCHAR(100)), '-', ''), '.', ''), ' ', ''), '/', ''), ',', ''), "
        f"'(', ''), ')', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), '')"
    )


def normalize_cedula(value):
    return re.sub(r"\D", "", str(value or ""))


def format_date(value):
    if not value:
        return ""
    raw = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw
    ddmmyyyy = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", raw)
    if ddmmyyyy:
        dd, mm, yyyy = ddmmyyyy.groups()
        return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
    return raw


def normalize_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    raw = str(value).strip()
    if not raw:
        return None
    cleaned = re.sub(r"[^\d,.\-]", "", raw)
    has_dot = "." in cleaned
    has_comma = "," in cleaned
    normalized = cleaned

    if has_dot and has_comma:
        normalized = cleaned.replace(".", "").replace(",", ".") if cleaned.rfind(",") > cleaned.rfind(".") else cleaned.replace(",", "")
    elif has_dot:
        if re.match(r"^\d{1,3}(\.\d{3})+$", cleaned) or cleaned.count(".") > 1 or re.match(r"^\d+\.\d{3}$", cleaned):
            normalized = cleaned.replace(".", "")
    elif has_comma:
        if re.match(r"^\d{1,3}(,\d{3})+$", cleaned) or cleaned.count(",") > 1 or re.match(r"^\d+,\d{3}$", cleaned):
            normalized = cleaned.replace(",", "")
        else:
            normalized = cleaned.replace(",", ".")

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def format_money(value):
    parsed = normalize_number(value)
    if parsed is None:
        return str(value or "").strip()
    quantized = parsed.quantize(Decimal("0.01")) if parsed % 1 else parsed.quantize(Decimal("1"))
    return f"{quantized:,.2f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")


def has_executed_value(value):
    parsed = normalize_number(value)
    return parsed is not None and parsed != 0


def normalize_key(key):
    return re.sub(r"\s+", " ", str(key or "")).strip().upper()


def normalize_text_for_dedup(text):
    value = unicodedata.normalize("NFD", str(text or ""))
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip().upper()


def find_column(columns, expected_names):
    normalized = [{"original": c, "normalized": normalize_key(c)} for c in columns]
    for expected in expected_names:
        target = normalize_key(expected)
        for item in normalized:
            if item["normalized"] == target:
                return item["original"]
    return None


def get_tables_metadata():
    now = int(time() * 1000)
    with _cache_lock:
        if _metadata_cache["tables"] is not None and now < _metadata_cache["expires_at"]:
            return _metadata_cache["tables"]

    sql_text = """
        SELECT t.table_name, c.column_name
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c
          ON c.table_schema = t.table_schema
         AND c.table_name = t.table_name
        WHERE t.table_schema = %s
          AND t.table_name LIKE 'contratos[_][0-9][0-9][0-9][0-9]'
          AND TRY_CONVERT(INT, RIGHT(t.table_name, 4)) <= %s
        ORDER BY t.table_name, c.ordinal_position
    """
    by_table = {}
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(sql_text, [DB_SCHEMA, DB_MAX_CONTRACT_YEAR])
        for table_name, column_name in cursor.fetchall():
            by_table.setdefault(table_name, [])
            if column_name:
                by_table[table_name].append(column_name)

    tables = [{"name": name, "columns": cols} for name, cols in by_table.items()]
    with _cache_lock:
        _metadata_cache["tables"] = tables
        _metadata_cache["expires_at"] = now + DB_METADATA_CACHE_TTL_MS
    return tables


def query_contracts_by_table(table_name, columns, cedula, cedula_alt):
    column_map = {
        "nombre": find_column(columns, ["RAZON SOCIAL", "razon_social"]),
        "cedula": find_column(columns, ["CEDULA", "cedula_nit"]),
        "cedula_digits": find_column(columns, ["cedula_nit_digits", "CEDULA_NIT_DIGITS"]),
        "objeto_ctto": find_column(columns, ["OBJETO CTTO", "objeto_ctto"]),
        "tipo_vinculacion": find_column(columns, ["TIPO VINCULACION", "TIPO VINCULACION "]),
        "contrato_no": find_column(columns, ["NO", "NO CONTRATO", "no_contrato"]),
        "firma_contrato": find_column(columns, ["FIRMA CONTRATO", "FECHA FIRMA", "fecha_firma"]),
        "fecha_inicio": find_column(columns, ["F. INICIO", "FECHA INICIO", "fecha_inicio"]),
        "fecha_terminacion": find_column(columns, ["F.TERM.", "FECHA TERM", "fecha_term"]),
        "valor": find_column(columns, ["VALOR CTO", "valor_cto"]),
        "valor_ejecutado": find_column(columns, ["VALOREJECUTADO", "valorejecutado", "valor_ejecutado"]),
    }
    required = ["nombre", "cedula", "contrato_no", "valor"]
    if not all(column_map[key] for key in required):
        return []

    q = quote_identifier
    table_ref = f"{q(DB_SCHEMA)}.{q(table_name)}"

    def select_or_null(key, alias):
        return f"{q(column_map[key])} AS {alias}" if column_map[key] else f"CAST(NULL AS NVARCHAR(MAX)) AS {alias}"

    select_sql = f"""
        SELECT
          {q(column_map['nombre'])} AS nombre,
          {q(column_map['cedula'])} AS cedula,
          {select_or_null('objeto_ctto', 'objeto_ctto')},
          {select_or_null('tipo_vinculacion', 'tipo_vinculacion')},
          {q(column_map['contrato_no'])} AS contrato_no,
          {select_or_null('firma_contrato', 'firma_contrato')},
          {select_or_null('fecha_inicio', 'fecha_inicio')},
          {select_or_null('fecha_terminacion', 'fecha_terminacion')},
          {q(column_map['valor'])} AS valor,
          {select_or_null('valor_ejecutado', 'valorejecutado')}
        FROM {table_ref}
    """
    raw_sql = f"{select_sql} WHERE CAST({q(column_map['cedula'])} AS NVARCHAR(100)) IN (%s, %s)"

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(raw_sql, [cedula, cedula_alt])
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        raw = [dict(zip(cols, row)) for row in rows]
        if raw:
            return raw

        normalized_filter = (
            f"{q(column_map['cedula_digits'])} IN (%s, %s)"
            if column_map["cedula_digits"]
            else f"{build_digits_only_sql(q(column_map['cedula']))} IN (%s, %s)"
        )
        normalized_sql = f"{select_sql} WHERE {normalized_filter}"
        cursor.execute(normalized_sql, [cedula, cedula_alt])
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]


def get_grouped_contracts_by_cedula(cedula_input):
    cedula = normalize_cedula(cedula_input)
    cedula_alt = re.sub(r"^0+", "", cedula) or cedula
    tables = get_tables_metadata()

    if not tables:
        raise ValueError(f"No se encontraron tablas contratos_YYYY en esquema {DB_SCHEMA} de la base actual.")

    rows = []
    for table in tables:
        rows.extend(query_contracts_by_table(table["name"], table["columns"], cedula, cedula_alt))

    rows = [row for row in rows if row.get("valorejecutado") is None or has_executed_value(row.get("valorejecutado"))]
    if not rows:
        raise ValueError(f"No se encontraron contratos válidos para la cédula {cedula_input}.")

    first = rows[0]
    objetos_unicos = []
    objetos_vistos = set()
    for item in rows:
        objeto = str(item.get("objeto_ctto") or "").replace('"', "").strip()
        if not objeto:
            continue
        normalized = normalize_text_for_dedup(objeto)
        if normalized in objetos_vistos:
            continue
        objetos_vistos.add(normalized)
        objetos_unicos.append(objeto)

    cargo_fallback = str(first.get("tipo_vinculacion") or "").replace('"', "").strip()
    cargo_completo = ", ".join(objetos_unicos) if objetos_unicos else cargo_fallback

    contratos = []
    for item in rows:
        contrato_no = str(item.get("contrato_no") or "").strip()
        firma = format_date(item.get("firma_contrato"))
        inicio = format_date(item.get("fecha_inicio"))
        fin = format_date(item.get("fecha_terminacion"))
        valor = format_money(item.get("valor"))
        contratos.append(
            {
                "contratoNo": contrato_no,
                "firmaContrato": firma,
                "fechaInicio": inicio,
                "fechaTerminacion": fin,
                "valor": valor,
                "no_contrato": contrato_no,
                "fecha_firma": firma,
                "fecha_inicio": inicio,
                "fecha_terminacion": fin,
                "valor_cto": valor,
            }
        )

    return {
        "nombre": str(first.get("nombre") or "").strip(),
        "cedula": normalize_cedula(first.get("cedula")),
        "cargo": cargo_completo,
        "objeto_ctto": cargo_completo,
        "contratos": contratos,
    }
