"""
Filtri personalizzati per API Documenti
"""
import django_filters
from documenti.models import Documento


class DocumentoFilter(django_filters.FilterSet):
    """
    FilterSet personalizzato per Documenti con supporto per lookup avanzati
    """
    # Filtri standard
    tipo = django_filters.NumberFilter(field_name='tipo')
    cliente = django_filters.NumberFilter(field_name='cliente')
    fascicolo = django_filters.NumberFilter(field_name='fascicolo')
    fascicolo__isnull = django_filters.BooleanFilter(field_name='fascicolo', lookup_expr='isnull')
    stato = django_filters.CharFilter(field_name='stato')
    digitale = django_filters.BooleanFilter(field_name='digitale')
    tracciabile = django_filters.BooleanFilter(field_name='tracciabile')
    ubicazione = django_filters.NumberFilter(field_name='ubicazione')
    out_aperto = django_filters.BooleanFilter(field_name='out_aperto')
    
    # Filtri per date
    data_da = django_filters.DateFilter(field_name='data_documento', lookup_expr='gte')
    data_a = django_filters.DateFilter(field_name='data_documento', lookup_expr='lte')
    
    class Meta:
        model = Documento
        fields = [
            'tipo', 'cliente', 'fascicolo', 'stato', 'digitale', 
            'tracciabile', 'ubicazione', 'out_aperto'
        ]
