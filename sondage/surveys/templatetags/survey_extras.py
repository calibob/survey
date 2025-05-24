from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """Multiplier le premier argument par le second"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
