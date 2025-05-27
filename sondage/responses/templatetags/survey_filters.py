from django import template

register = template.Library()

@register.filter(name='mul')
def multiply(value, arg):
    """Filtre pour multiplier la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
