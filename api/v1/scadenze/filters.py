"""
Filtri personalizzati per API Scadenze
"""
import django_filters
from scadenze.models import Scadenza, ScadenzaOccorrenza, ScadenzaAlert


class ScadenzaOccorrenzaFilter(django_filters.FilterSet):
    """
    Filtro personalizzato per ScadenzaOccorrenza con supporto per:
    - Filtri di data (gte, lte, lt, gt)
    - Filtro multiplo per stato (stato__in)
    - Filtro per scadenza, metodo_alert
    """
    
    # Filtri per data inizio
    inizio__gte = django_filters.DateTimeFilter(field_name='inizio', lookup_expr='gte')
    inizio__lte = django_filters.DateTimeFilter(field_name='inizio', lookup_expr='lte')
    inizio__lt = django_filters.DateTimeFilter(field_name='inizio', lookup_expr='lt')
    inizio__gt = django_filters.DateTimeFilter(field_name='inizio', lookup_expr='gt')
    
    # Filtri per data fine
    fine__gte = django_filters.DateTimeFilter(field_name='fine', lookup_expr='gte')
    fine__lte = django_filters.DateTimeFilter(field_name='fine', lookup_expr='lte')
    fine__lt = django_filters.DateTimeFilter(field_name='fine', lookup_expr='lt')
    fine__gt = django_filters.DateTimeFilter(field_name='fine', lookup_expr='gt')
    
    # Filtro multiplo per stato (es: stato__in=pending,scheduled)
    stato__in = django_filters.CharFilter(method='filter_stato_in')
    
    # Filtri standard
    scadenza = django_filters.NumberFilter(field_name='scadenza__id')
    metodo_alert = django_filters.CharFilter(field_name='metodo_alert')
    stato = django_filters.CharFilter(field_name='stato')
    
    class Meta:
        model = ScadenzaOccorrenza
        fields = ['scadenza', 'stato', 'metodo_alert']
    
    def filter_stato_in(self, queryset, name, value):
        """
        Filtro personalizzato per stato__in che supporta valori separati da virgola.
        Es: stato__in=pending,scheduled,completed
        """
        if not value:
            return queryset
        
        # Split dei valori separati da virgola
        stati = [s.strip() for s in value.split(',')]
        return queryset.filter(stato__in=stati)


class ScadenzaFilter(django_filters.FilterSet):
    """
    Filtro personalizzato per Scadenza
    """
    
    # Filtri di testo
    titolo__icontains = django_filters.CharFilter(field_name='titolo', lookup_expr='icontains')
    descrizione__icontains = django_filters.CharFilter(field_name='descrizione', lookup_expr='icontains')
    categoria__icontains = django_filters.CharFilter(field_name='categoria', lookup_expr='icontains')
    
    # Filtri multipli
    stato__in = django_filters.CharFilter(method='filter_stato_in')
    priorita__in = django_filters.CharFilter(method='filter_priorita_in')
    periodicita__in = django_filters.CharFilter(method='filter_periodicita_in')
    
    # Filtri relazioni
    creato_da = django_filters.NumberFilter(field_name='creato_da__id')
    assegnatari = django_filters.NumberFilter(field_name='assegnatari__id')
    pratiche = django_filters.NumberFilter(field_name='pratiche__id')
    fascicoli = django_filters.NumberFilter(field_name='fascicoli__id')
    documenti = django_filters.NumberFilter(field_name='documenti__id')
    
    class Meta:
        model = Scadenza
        fields = ['stato', 'priorita', 'periodicita', 'categoria']
    
    def filter_stato_in(self, queryset, name, value):
        """Filtro multiplo per stato"""
        if not value:
            return queryset
        stati = [s.strip() for s in value.split(',')]
        return queryset.filter(stato__in=stati)
    
    def filter_priorita_in(self, queryset, name, value):
        """Filtro multiplo per priorità"""
        if not value:
            return queryset
        priorita = [p.strip() for p in value.split(',')]
        return queryset.filter(priorita__in=priorita)
    
    def filter_periodicita_in(self, queryset, name, value):
        """Filtro multiplo per periodicità"""
        if not value:
            return queryset
        periodicita = [p.strip() for p in value.split(',')]
        return queryset.filter(periodicita__in=periodicita)


class ScadenzaAlertFilter(django_filters.FilterSet):
    """
    Filtro personalizzato per ScadenzaAlert
    """
    
    scadenza = django_filters.NumberFilter(method='filter_scadenza')
    occorrenza = django_filters.NumberFilter(field_name='occorrenza__id')
    metodo_alert__in = django_filters.CharFilter(method='filter_metodo_in')
    stato__in = django_filters.CharFilter(method='filter_stato_in')
    
    class Meta:
        model = ScadenzaAlert
        fields = ['occorrenza', 'metodo_alert', 'stato', 'offset_alert_periodo']
    
    def filter_scadenza(self, queryset, name, value):
        """Filtro per scadenza attraverso occorrenza"""
        if not value:
            return queryset
        return queryset.filter(occorrenza__scadenza__id=value)
    
    def filter_metodo_in(self, queryset, name, value):
        """Filtro multiplo per metodo_alert"""
        if not value:
            return queryset
        metodi = [m.strip() for m in value.split(',')]
        return queryset.filter(metodo_alert__in=metodi)
    
    def filter_stato_in(self, queryset, name, value):
        """Filtro multiplo per stato"""
        if not value:
            return queryset
        stati = [s.strip() for s in value.split(',')]
        return queryset.filter(stato__in=stati)
