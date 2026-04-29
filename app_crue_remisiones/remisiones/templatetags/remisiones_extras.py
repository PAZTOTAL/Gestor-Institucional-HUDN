"""
Filtros de template personalizados para la app remisiones.
"""
from django import template

from remisiones.utils import truncar_para_tabla as _truncar_para_tabla

register = template.Library()


@register.filter(name='truncar_para_tabla')
def truncar_para_tabla(texto, max_chars=50):
    """
    Filtro de template: trunca texto a max_chars caracteres + '…'.

    Uso en template:
        {{ remision.DIAGNOSTICO|truncar_para_tabla }}
        {{ remision.DIAGNOSTICO|truncar_para_tabla:30 }}
    """
    return _truncar_para_tabla(texto, max_chars)
