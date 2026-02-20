"""
Utility per gestione cache Redis
Fornisce decoratori e funzioni helper per il caching efficiente
"""
from functools import wraps
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import hashlib
import json


def cache_key_generator(*args, **kwargs):
    """
    Genera una chiave di cache univoca basata su argomenti
    """
    key_data = {
        'args': str(args),
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_view(timeout=300, key_prefix=None):
    """
    Decoratore per cachare viste basate su funzioni
    
    Usage:
        @cache_view(timeout=600, key_prefix='my_view')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Genera chiave cache
            cache_key = f"{key_prefix or view_func.__name__}:{request.path}:{request.GET.urlencode()}"
            
            # Cerca in cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Esegui vista e salva in cache
            response = view_func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            return response
        
        return wrapper
    return decorator


def cached_model_property(timeout=300):
    """
    Decoratore per cachare property di modelli
    
    Usage:
        class MyModel(models.Model):
            @cached_model_property(timeout=600)
            def expensive_calculation(self):
                ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self):
            cache_key = f"model:{self.__class__.__name__}:{self.pk}:{func.__name__}"
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            value = func(self)
            cache.set(cache_key, value, timeout)
            return value
        
        return property(wrapper)
    return decorator


def invalidate_model_cache(instance, *property_names):
    """
    Invalida la cache per specifiche property di un modello
    
    Usage:
        invalidate_model_cache(my_instance, 'expensive_calculation', 'other_property')
    """
    for prop_name in property_names:
        cache_key = f"model:{instance.__class__.__name__}:{instance.pk}:{prop_name}"
        cache.delete(cache_key)


def cache_queryset(queryset_func, timeout=300, key_prefix=None):
    """
    Cache il risultato di una queryset
    
    Usage:
        def get_active_users():
            return User.objects.filter(is_active=True)
        
        cached_users = cache_queryset(get_active_users, timeout=600, key_prefix='active_users')
    """
    cache_key = key_prefix or f"queryset:{queryset_func.__name__}"
    
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    result = list(queryset_func())
    cache.set(cache_key, result, timeout)
    return result


class CachedClassBasedView:
    """
    Mixin per aggiungere caching a class-based views
    
    Usage:
        class MyView(CachedClassBasedView, ListView):
            cache_timeout = 600
            cache_key_prefix = 'my_list'
    """
    cache_timeout = 300
    cache_key_prefix = None
    
    @method_decorator(cache_page(300))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# Funzioni helper per operazioni cache comuni

def get_or_set_cache(key, callable_func, timeout=300):
    """
    Get from cache o esegui funzione e salva risultato
    """
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache.set(key, result, timeout)
    return result


def delete_pattern(pattern):
    """
    Elimina tutte le chiavi che matchano un pattern
    Richiede Redis (non funziona con altri backend)
    """
    from django_redis import get_redis_connection
    conn = get_redis_connection("default")
    keys = conn.keys(f"mygest:{pattern}*")
    if keys:
        conn.delete(*keys)


def clear_all_cache():
    """
    Svuota completamente la cache
    """
    cache.clear()


# Template tag helper per caching in template
def cache_fragment(fragment_name, timeout=300):
    """
    Usa nei template:
    {% load cache %}
    {% cache 600 sidebar user.id %}
        ... expensive template code ...
    {% endcache %}
    """
    pass
