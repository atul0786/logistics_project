
from django import template

register = template.Library()

@register.filter(name='get')
def get(dictionary, key):
    """Dictionary me se key ka value return karega"""
    return dictionary.get(key, "N/A") if isinstance(dictionary, dict) else "N/A"
