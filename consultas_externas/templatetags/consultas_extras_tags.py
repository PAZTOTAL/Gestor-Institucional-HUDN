from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """Obtiene un atributo de un objeto dinámicamente."""
    if hasattr(obj, attr_name):
        val = getattr(obj, attr_name)
        if val is None:
            return ""
        return val
    return ""
