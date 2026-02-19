"""
API v1 Views
"""
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_simple(request):
    """Simple test endpoint"""
    return Response({
        'pratiche_attive': 10,
        'pratiche_chiuse': 20,
        'documenti_count': 30,
        'scadenze_oggi': 2,
        'clienti_attivi': 15,
        'pratiche_per_mese': [
            {'mese': 'Giu', 'count': 10},
            {'mese': 'Lug', 'count': 15},
            {'mese': 'Ago', 'count': 12},
            {'mese': 'Set', 'count': 18},
            {'mese': 'Ott', 'count': 20},
            {'mese': 'Nov', 'count': 14},
        ],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Dashboard statistics endpoint with real data"""
    from pratiche.models import Pratica
    from documenti.models import Documento
    from scadenze.models import Scadenza
    from anagrafiche.models import Cliente
    
    try:
        today = timezone.now().date()
        
        # Statistiche Pratiche
        try:
            pratiche_attive = Pratica.objects.filter(stato__in=['aperta', 'lavorazione', 'attesa']).count()
            pratiche_chiuse = Pratica.objects.filter(stato='chiusa').count()
        except Exception as e:
            print(f"Error querying Pratica: {e}")
            pratiche_attive = 0
            pratiche_chiuse = 0
        
        # Statistiche Documenti
        try:
            documenti_count = Documento.objects.count()
        except Exception as e:
            print(f"Error querying Documento: {e}")
            documenti_count = 0
        
        # Scadenze oggi
        try:
            scadenze_oggi = Scadenza.objects.filter(
                stato='attiva'
            ).count()
        except Exception as e:
            print(f"Error querying Scadenza: {e}")
            scadenze_oggi = 0
        
        # Clienti attivi (con almeno una pratica negli ultimi 6 mesi)
        try:
            sei_mesi_fa = today - timedelta(days=180)
            clienti_attivi = Cliente.objects.filter(
                pratiche__data_apertura__gte=sei_mesi_fa
            ).distinct().count()
        except Exception as e:
            print(f"Error querying Cliente: {e}")
            clienti_attivi = 0
        
        # Pratiche per mese (ultimi 6 mesi)
        pratiche_per_mese = []
        mesi_ita = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        
        try:
            for i in range(5, -1, -1):
                data = today - timedelta(days=30*i)
                mese_num = data.month - 1
                count = Pratica.objects.filter(
                    data_apertura__year=data.year,
                    data_apertura__month=data.month
                ).count()
                pratiche_per_mese.append({
                    'mese': mesi_ita[mese_num],
                    'count': count
                })
        except Exception as e:
            print(f"Error building pratiche_per_mese: {e}")
            pratiche_per_mese = [{'mese': m, 'count': 0} for m in ['Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov']]
        
        return Response({
            'pratiche_attive': pratiche_attive,
            'pratiche_chiuse': pratiche_chiuse,
            'documenti_count': documenti_count,
            'scadenze_oggi': scadenze_oggi,
            'clienti_attivi': clienti_attivi,
            'pratiche_per_mese': pratiche_per_mese,
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"FATAL ERROR in dashboard_stats: {e}")
        print(error_trace)
        return Response({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': error_trace
        }, status=500)
