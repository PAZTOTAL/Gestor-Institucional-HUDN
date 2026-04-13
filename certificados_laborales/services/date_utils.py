from datetime import datetime

MONTHS_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def get_spanish_expedition_date(now=None):
    current = now or datetime.now()
    dia = current.day
    mes = MONTHS_ES[current.month - 1]
    anio = current.year
    return {
        "dia": dia,
        "mes": mes,
        "anio": anio,
        "fecha_texto": f"Se expide la presente certificación a los {dia} días del mes de {mes} del año {anio}",
    }
