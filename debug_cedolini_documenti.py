"""
Verifica documenti cedolini reali per capire il problema.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import Documento, DocumentiTipo, AttributoValore

# Trova documenti BPAG recenti
try:
    tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
    documenti = Documento.objects.filter(tipo=tipo_bpag).order_by('-creato_il')[:5]
    
    print(f"Ultimi 5 documenti BPAG:")
    print("=" * 80)
    
    for doc in documenti:
        print(f"\nID: {doc.id}")
        print(f"Codice: {doc.codice}")
        print(f"Descrizione: {doc.descrizione}")
        print(f"File: {doc.file.name if doc.file else 'N/A'}")
        print(f"Cliente: {doc.cliente}")
        
        # Mostra attributi
        print(f"Attributi:")
        attributi = AttributoValore.objects.filter(documento=doc).select_related('definizione')
        for av in attributi:
            print(f"  - {av.definizione.codice}: {av.valore}")
        
        print("-" * 80)
        
except Exception as e:
    print(f"Errore: {e}")
    import traceback
    traceback.print_exc()
