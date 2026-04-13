from django import template

register = template.Library()

@register.filter
def replace_underscore(value, arg):
    return value.replace('_', arg)
