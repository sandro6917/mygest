from django import template
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from scadenze.models import ScadenzaOccorrenza, ScadenzaAlert

register = template.Library()


@register.inclusion_tag('scadenze/widgets/dashboard_widget.html', takes_context=False)
def scadenze_dashboard_widget():
    """Widget scadenze per dashboard con statistiche."""
    
    oggi = timezone.now()
    domani = oggi + timedelta(days=1)
    settimana = oggi + timedelta(days=7)
    
    # Occorrenze prossime (prossimi 7 giorni)
    occorrenze_prossime = ScadenzaOccorrenza.objects.filter(
        inizio__gte=oggi,
        inizio__lt=settimana,
        stato__in=[
            ScadenzaOccorrenza.Stato.PENDENTE,
            ScadenzaOccorrenza.Stato.PROGRAMMATA,
        ]
    ).select_related('scadenza').prefetch_related('alerts', 'scadenza__pratiche').order_by('inizio')[:5]
    
    # Statistiche
    oggi_count = ScadenzaOccorrenza.objects.filter(
        inizio__gte=oggi.replace(hour=0, minute=0, second=0, microsecond=0),
        inizio__lt=domani.replace(hour=0, minute=0, second=0, microsecond=0),
        stato__in=[ScadenzaOccorrenza.Stato.PENDENTE, ScadenzaOccorrenza.Stato.PROGRAMMATA]
    ).count()
    
    settimana_count = ScadenzaOccorrenza.objects.filter(
        inizio__gte=oggi,
        inizio__lt=settimana,
        stato__in=[ScadenzaOccorrenza.Stato.PENDENTE, ScadenzaOccorrenza.Stato.PROGRAMMATA]
    ).count()
    
    critiche_count = ScadenzaOccorrenza.objects.filter(
        inizio__gte=oggi,
        inizio__lt=settimana,
        scadenza__priorita='critical',
        stato__in=[ScadenzaOccorrenza.Stato.PENDENTE, ScadenzaOccorrenza.Stato.PROGRAMMATA]
    ).count()
    
    alert_pendenti_count = ScadenzaAlert.objects.filter(
        alert_programmata_il__lte=oggi,
        stato=ScadenzaAlert.Stato.PENDENTE
    ).count()
    
    return {
        'occorrenze': occorrenze_prossime,
        'oggi_count': oggi_count,
        'settimana_count': settimana_count,
        'critiche_count': critiche_count,
        'alert_pendenti_count': alert_pendenti_count,
        'scadenziario_url': reverse('scadenze:scadenziario'),
        'calendario_url': reverse('scadenze:calendario_visual'),
        'create_url': reverse('scadenze:create'),
    }
