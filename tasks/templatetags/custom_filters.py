from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Devuelve el valor de una clave específica en un diccionario."""
    return dictionary.get(key, 0)
