from django import template
from django.utils.formats import number_format

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Formatea un número como moneda colombiana con separadores de miles (punto) 
    y decimales (coma).
    Ejemplo: 2231954118.00 -> 2.231.954.118,00
    """
    try:
        # Convertir a float si es necesario
        value = float(value)
        
        # Separar parte entera y decimal
        integer_part = int(value)
        decimal_part = int(round((value - integer_part) * 100))
        
        # Formatear parte entera con separador de miles (punto)
        integer_str = f"{integer_part:,}".replace(',', '.')
        
        # Formatear parte decimal con dos dígitos
        decimal_str = f"{decimal_part:02d}"
        
        return f"{integer_str},{decimal_str}"
    except (ValueError, TypeError):
        return value
