"""
Template tags personalizzati per caching e ottimizzazione
"""
from django import template
from django.core.cache import cache

register = template.Library()


@register.simple_tag
def cache_get(key):
    """
    Ottieni valore dalla cache
    Usage: {% cache_get 'my_key' as my_value %}
    """
    return cache.get(key)


@register.simple_tag
def cache_set(key, value, timeout=300):
    """
    Salva valore in cache
    Usage: {% cache_set 'my_key' my_value 600 %}
    """
    cache.set(key, value, timeout)
    return ''


@register.filter
def cached(value, key):
    """
    Filter per cachare un valore
    Usage: {{ expensive_value|cached:'my_cache_key' }}
    """
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value
    
    cache.set(key, value, 300)
    return value
