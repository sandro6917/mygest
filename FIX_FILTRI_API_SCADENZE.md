# Fix Filtri API Scadenze Occorrenze

## 📋 Problema Risolto

La richiesta API:
```
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&stato__in=pending,scheduled&ordering=inizio&page_size=5
```

**Non stava filtrando correttamente** i risultati perché:
1. Il `ViewSet` usava `filterset_fields` semplici che non supportano lookup `__gte`, `__lt`, `__in`
2. Non c'era un `FilterSet` personalizzato per gestire filtri complessi
3. I filtri per data venivano ignorati
4. Il filtro `stato__in=pending,scheduled` non funzionava (valori multipli non supportati)

**Risultato**: L'API restituiva tutte le 70 occorrenze invece di filtrare correttamente.

## ✅ Soluzione Implementata

### 1. Creato FilterSet Personalizzato (`api/v1/scadenze/filters.py`)

```python
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
    
    def filter_stato_in(self, queryset, name, value):
        """Split dei valori separati da virgola"""
        if not value:
            return queryset
        stati = [s.strip() for s in value.split(',')]
        return queryset.filter(stato__in=stati)
```

### 2. Aggiornato ViewSet (`api/v1/scadenze/views.py`)

**Prima**:
```python
class ScadenzaOccorrenzaViewSet(viewsets.ModelViewSet):
    filterset_fields = ['scadenza', 'stato', 'metodo_alert']  # ❌ Non supporta __gte, __in
```

**Dopo**:
```python
class ScadenzaOccorrenzaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione occorrenze con filtri avanzati.
    
    ## Filtri Supportati
    - inizio__gte, inizio__lte, inizio__lt, inizio__gt: filtri per data
    - stato__in: filtro multiplo per stato (es: pending,scheduled)
    - scadenza: ID della scadenza
    - ordering: ordinamento (es: ordering=inizio)
    """
    filterset_class = ScadenzaOccorrenzaFilter  # ✅ Filtri avanzati
```

### 3. Implementati Filtri Anche per Altri ViewSets

- **ScadenzaFilter**: Filtri avanzati per scadenze (stato__in, priorita__in, etc.)
- **ScadenzaAlertFilter**: Filtri per alert (metodo_alert__in, stato__in, etc.)

### 4. Creati Test Completi (`api/v1/scadenze/tests/test_occorrenza_filters.py`)

10 test che verificano:
- ✅ Filtro singolo stato
- ✅ Filtro multiplo stati (`stato__in=pending,scheduled`)
- ✅ Filtro data `inizio__gte`
- ✅ Filtro data `inizio__lt`
- ✅ Filtro range di date
- ✅ Filtro combinato (data + stato)
- ✅ Filtro per scadenza
- ✅ Ordinamento
- ✅ Paginazione
- ✅ Risultato vuoto con filtri stretti

**Risultato test**: ✅ **10/10 passed**

## 🎯 Benefici

### Prima del Fix
```bash
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&stato__in=pending,scheduled

# Restituiva: TUTTE le 70 occorrenze (filtri ignorati)
# Response size: 21KB
```

### Dopo il Fix
```bash
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&stato__in=pending,scheduled

# Restituisce: Solo le occorrenze che matchano i filtri (0 nel caso specifico)
# Response size: ~200 bytes
# Performance: Molto più veloce, query ottimizzata
```

## 📚 Filtri Disponibili

### ScadenzaOccorrenza

#### Filtri Data:
- `inizio__gte`: Data inizio >= (es: `2026-01-23`)
- `inizio__lte`: Data inizio <=
- `inizio__lt`: Data inizio <
- `inizio__gt`: Data inizio >
- `fine__gte`, `fine__lte`, `fine__lt`, `fine__gt`: Analoghi per data fine

#### Filtri Stato:
- `stato`: Singolo stato (es: `pending`)
- `stato__in`: Multipli stati (es: `pending,scheduled,completed`)

#### Altri:
- `scadenza`: ID scadenza
- `metodo_alert`: Metodo alert

#### Ordinamento:
- `ordering`: Campi disponibili: `inizio`, `fine`, `creato_il`
- Esempio: `ordering=inizio` (ascendente), `ordering=-inizio` (discendente)

### Esempi di Uso

```bash
# Occorrenze pending nella prossima settimana
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&stato__in=pending,scheduled

# Occorrenze di una specifica scadenza
GET /api/v1/scadenze/occorrenze/?scadenza=5

# Occorrenze completate ordinate per data (più recenti prima)
GET /api/v1/scadenze/occorrenze/?stato=completed&ordering=-inizio

# Occorrenze con alert email nei prossimi 7 giorni
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&metodo_alert=email

# Combina filtri multipli
GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-01&stato__in=pending,scheduled&ordering=inizio&page_size=10
```

## 📊 Database - Scadenze Pending

**Situazione Attuale** (70 occorrenze pending):

1. **Scadenze Passate Critiche** (da gestire):
   - Scadenza pagamento cartella (02/03/2024)
   - Deposito Bilanci 2020, 2021, 2023 (31/10/2025)
   - Termine invio 770 2025 (31/10/2025)
   - Pagamento cartella 770 2021 (22/12/2025)

2. **Scadenze Future Ricorrenti**:
   - Presentazione documenti compliance (mensile, giorno 19)
   - Liquidazioni periodiche IVA (trimestrale)

## 🔧 File Modificati

1. **Nuovo**: `api/v1/scadenze/filters.py` - FilterSet personalizzati
2. **Modificato**: `api/v1/scadenze/views.py` - Aggiunto `filterset_class` ai ViewSets
3. **Nuovo**: `api/v1/scadenze/tests/test_occorrenza_filters.py` - Test completi

## 🚀 Deploy

Il server Django è stato riavviato automaticamente (HUP signal) e i nuovi filtri sono già attivi.

## ✅ Checklist

- [x] Creato FilterSet personalizzato con tutti i filtri necessari
- [x] Aggiornato ViewSet per usare FilterSet
- [x] Documentata API con esempi
- [x] Creati test completi (10/10 passed)
- [x] Verificato funzionamento con database reale
- [x] Server riavviato e modifiche attive

## 📝 Note Tecniche

- I filtri usano `django-filters` per parsing automatico delle date
- Il filtro `stato__in` supporta valori separati da virgola
- L'ordinamento è configurabile tramite `ordering` parameter
- La paginazione funziona automaticamente con il sistema REST framework
- Le query sono ottimizzate con `select_related('scadenza')`

---

**Data**: 23 Gennaio 2026
**Versione**: 1.0
**Status**: ✅ Completato e Testato
