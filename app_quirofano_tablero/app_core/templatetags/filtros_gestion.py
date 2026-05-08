from django import template

register = template.Library ()


@register.filter
def get_item (diccionario, clave):
	"""Retorna el valor de un diccionario dado su clave, intentando también con str(clave)."""
	valor = diccionario.get (clave)
	if valor is None:
		valor = diccionario.get (str (clave))
	return valor
