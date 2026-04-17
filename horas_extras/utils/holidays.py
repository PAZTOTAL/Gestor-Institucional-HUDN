from datetime import date, timedelta


def calcular_pascua(year):
    """Calcula el Domingo de Pascua usando el algoritmo Gregoriano Anónimo."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def siguiente_lunes(fecha):
    """Retorna el siguiente lunes si la fecha no es lunes (Ley Emiliani)."""
    dias = (7 - fecha.weekday()) % 7
    if dias == 0:
        return fecha
    return fecha + timedelta(days=dias)


def festivos_colombia(year):
    """Retorna lista de festivos colombianos para el año dado."""
    pascua = calcular_pascua(year)

    festivos = [
        # Fijos
        (date(year, 1, 1), 'Año Nuevo'),
        (date(year, 5, 1), 'Día del Trabajo'),
        (date(year, 7, 20), 'Día de la Independencia'),
        (date(year, 8, 7), 'Batalla de Boyacá'),
        (date(year, 12, 8), 'Inmaculada Concepción'),
        (date(year, 12, 25), 'Navidad'),
        # Semana Santa (fijos respecto a Pascua)
        (pascua - timedelta(days=3), 'Jueves Santo'),
        (pascua - timedelta(days=2), 'Viernes Santo'),
        # Ley Emiliani (siguiente lunes)
        (siguiente_lunes(date(year, 1, 6)), 'Reyes Magos'),
        (siguiente_lunes(date(year, 3, 19)), 'San José'),
        (siguiente_lunes(pascua + timedelta(days=40)), 'Ascensión del Señor'),
        (siguiente_lunes(pascua + timedelta(days=60)), 'Corpus Christi'),
        (siguiente_lunes(pascua + timedelta(days=71)), 'Sagrado Corazón'),
        (siguiente_lunes(date(year, 6, 29)), 'San Pedro y San Pablo'),
        (siguiente_lunes(date(year, 8, 15)), 'Asunción de la Virgen'),
        (siguiente_lunes(date(year, 10, 12)), 'Día de la Raza'),
        (siguiente_lunes(date(year, 11, 1)), 'Todos los Santos'),
        (siguiente_lunes(date(year, 11, 11)), 'Independencia de Cartagena'),
    ]

    return {str(f[0]): f[1] for f in sorted(festivos, key=lambda x: x[0])}


def festivos_mes(year, month):
    """Retorna festivos de un mes específico."""
    todos = festivos_colombia(year)
    return {
        fecha: nombre
        for fecha, nombre in todos.items()
        if date.fromisoformat(fecha).month == month
    }


def es_festivo_o_domingo(fecha_str, festivos_dict):
    """Indica si una fecha es festivo o domingo."""
    fecha = date.fromisoformat(fecha_str)
    return fecha.weekday() == 6 or fecha_str in festivos_dict
