from django import template

register = template.Library()

@register.filter(name='get_form_field')
def get_form_field(form, field_name):
    """
    Retorna un campo del formulario por su nombre de cadena.
    Uso: {{ form|get_form_field:"campo_nombre" }}
    """
    try:
        # Si el field_name viene con 'form.' al inicio (por el add en el template)
        if field_name.startswith('form.'):
            field_name = field_name[5:]
        return form[field_name]
    except (KeyError, AttributeError):
        return None
