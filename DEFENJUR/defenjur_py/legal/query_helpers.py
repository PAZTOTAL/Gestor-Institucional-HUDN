"""
Consultas equivalentes a STR_TO_DATE / rangos de fechas en defenjur-back/controllers (MySQL).
En Django se usa SQL según el motor: SQL Server (TRY_CONVERT 103) o MySQL (STR_TO_DATE).
"""
import re
from django.db import connection


def parse_dmy(s):
    """Parse 'dd/mm/yyyy' → válido o None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100):
        return None
    from datetime import date
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def is_dmy_string(s):
    return parse_dmy(s) is not None


def _quoted(model, field_name):
    tbl = connection.ops.quote_name(model._meta.db_table)
    col = connection.ops.quote_name(field_name)
    return f'{tbl}.{col}'


def filter_charfield_dmy_range(queryset, field_name, fecha_inicio, fecha_fin):
    """
    Filtra registros donde el CharField fecha_inicio..fecha_fin (ambos dd/mm/yyyy) en BD.
    Paridad con getByDateRange de acciones_tutela.js y similares.
    """
    model = queryset.model
    fi, ff = (fecha_inicio or '').strip(), (fecha_fin or '').strip()
    if not fi or not ff:
        return queryset
    if not is_dmy_string(fi) or not is_dmy_string(ff):
        return queryset

    full = _quoted(model, field_name)
    vendor = connection.vendor

    if vendor == 'microsoft':
        return queryset.extra(
            where=[
                f'TRY_CONVERT(date, {full}, 103) >= TRY_CONVERT(date, %s, 103)',
                f'TRY_CONVERT(date, {full}, 103) <= TRY_CONVERT(date, %s, 103)',
            ],
            params=[fi, ff],
        )
    if vendor == 'mysql':
        return queryset.extra(
            where=[
                f"STR_TO_DATE({full}, '%%d/%%m/%%Y') >= STR_TO_DATE(%s, '%%d/%%m/%%Y')",
                f"STR_TO_DATE({full}, '%%d/%%m/%%Y') <= STR_TO_DATE(%s, '%%d/%%m/%%Y')",
            ],
            params=[fi, ff],
        )
    # SQLite u otros: filtro aproximado por orden lexicográfico no aplica; sin conversión
    return queryset


def filter_tutela_by_month_year(queryset, month: int, year: int):
    """Paridad con getByMonthYear (SUBSTRING fecha_llegada dd/mm/yyyy)."""
    if not (1 <= month <= 12 and 1900 <= year <= 2100):
        return queryset
    mm = str(month).zfill(2)
    return queryset.filter(fecha_llegada__contains=f'/{mm}/{year}')
