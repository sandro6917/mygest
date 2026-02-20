"""
Mixins e utility per ottimizzazione query e paginazione
"""
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.db.models import Prefetch
from rest_framework.pagination import PageNumberPagination


class OptimizedListView(ListView):
    """
    ListView ottimizzata con paginazione automatica e select_related
    
    Usage:
        class MyListView(OptimizedListView):
            model = MyModel
            template_name = 'my_template.html'
            paginate_by = 20
            select_related_fields = ['foreign_key_field']
            prefetch_related_fields = ['many_to_many_field']
    """
    paginate_by = 20
    select_related_fields = []
    prefetch_related_fields = []
    ordering = ['-id']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Applica select_related
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        
        # Applica prefetch_related
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        # Applica ordinamento
        if self.ordering:
            queryset = queryset.order_by(*self.ordering if isinstance(self.ordering, (list, tuple)) else [self.ordering])
        
        return queryset


class StandardPagination(PageNumberPagination):
    """
    Paginazione standard per API REST
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargePagination(PageNumberPagination):
    """
    Paginazione per liste grandi
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


def paginate_queryset(queryset, page_number, per_page=20):
    """
    Funzione helper per paginare una queryset manualmente
    
    Returns: (page_obj, paginator)
    """
    paginator = Paginator(queryset, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj, paginator


# ====================================
# QUERY OPTIMIZATION HELPERS
# ====================================

# Configurazioni comuni di select_related/prefetch_related per modelli

DOCUMENTO_RELATED = {
    'select_related': [
        'tipo',
        'cliente',
        'cliente__anagrafica',
        'fascicolo',
        'pratica',
        'pratica__cliente',
        'pratica__tipo',
    ],
    'prefetch_related': [
        'movimenti',
        'collocazioni',
    ]
}

PRATICA_RELATED = {
    'select_related': [
        'tipo',
        'cliente',
        'cliente__anagrafica',
    ],
    'prefetch_related': [
        Prefetch('note', to_attr='cached_note'),
        'relazioni',
        'documenti',
        'fascicoli',
    ]
}

FASCICOLO_RELATED = {
    'select_related': [
        'tipo',
        'cliente',
        'cliente__anagrafica',
        'classificazione',
    ],
    'prefetch_related': [
        Prefetch('pratiche', to_attr='cached_pratiche'),
        'documenti',
        'sotto_fascicoli',
    ]
}

MOVIMENTO_PROTOCOLLO_RELATED = {
    'select_related': [
        'content_type',
        'mittente',
        'destinatario',
    ],
    'prefetch_related': []
}

SCADENZA_RELATED = {
    'select_related': [
        'pratica',
        'pratica__cliente',
        'cliente',
    ],
    'prefetch_related': [
        'occorrenze',
    ]
}


def optimize_queryset(queryset, related_config):
    """
    Applica ottimizzazioni a una queryset usando una configurazione
    
    Usage:
        qs = Documento.objects.all()
        qs = optimize_queryset(qs, DOCUMENTO_RELATED)
    """
    if related_config.get('select_related'):
        queryset = queryset.select_related(*related_config['select_related'])
    
    if related_config.get('prefetch_related'):
        queryset = queryset.prefetch_related(*related_config['prefetch_related'])
    
    return queryset


def get_optimized_documento_qs(base_qs=None):
    """Helper per ottenere queryset ottimizzata di Documenti"""
    from documenti.models import Documento
    qs = base_qs or Documento.objects.all()
    return optimize_queryset(qs, DOCUMENTO_RELATED)


def get_optimized_pratica_qs(base_qs=None):
    """Helper per ottenere queryset ottimizzata di Pratiche"""
    from pratiche.models import Pratica
    qs = base_qs or Pratica.objects.all()
    return optimize_queryset(qs, PRATICA_RELATED)


def get_optimized_fascicolo_qs(base_qs=None):
    """Helper per ottenere queryset ottimizzata di Fascicoli"""
    from fascicoli.models import Fascicolo
    qs = base_qs or Fascicolo.objects.all()
    return optimize_queryset(qs, FASCICOLO_RELATED)


def get_optimized_movimento_qs(base_qs=None):
    """Helper per ottenere queryset ottimizzata di Movimenti Protocollo"""
    from protocollo.models import MovimentoProtocollo
    qs = base_qs or MovimentoProtocollo.objects.all()
    return optimize_queryset(qs, MOVIMENTO_PROTOCOLLO_RELATED)


def get_optimized_scadenza_qs(base_qs=None):
    """Helper per ottenere queryset ottimizzata di Scadenze"""
    from scadenze.models import Scadenza
    qs = base_qs or Scadenza.objects.all()
    return optimize_queryset(qs, SCADENZA_RELATED)


# ====================================
# QUERY ANALYSIS HELPERS (per sviluppo)
# ====================================

def count_queries(func):
    """
    Decoratore per contare le query eseguite da una funzione (solo in DEBUG)
    
    Usage:
        @count_queries
        def my_view(request):
            ...
    """
    from functools import wraps
    from django.conf import settings
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        from django.db import connection, reset_queries
        
        reset_queries()
        result = func(*args, **kwargs)
        
        queries = len(connection.queries)
        print(f"\n{'='*60}")
        print(f"Function: {func.__name__}")
        print(f"Queries executed: {queries}")
        if queries > 50:
            print("⚠️  WARNING: High number of queries detected!")
            print("Consider using select_related/prefetch_related")
        print(f"{'='*60}\n")
        
        return result
    
    return wrapper


def log_queries(queryset):
    """
    Log delle query SQL che verranno eseguite da una queryset (solo in DEBUG)
    """
    from django.conf import settings
    
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"Queryset: {queryset.model.__name__}")
        print(f"SQL: {queryset.query}")
        print(f"{'='*60}\n")
