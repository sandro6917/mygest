#!/usr/bin/env python
"""
Test estrazione CU con template AI.
Verifica quali dati vengono estratti dalle zone definite nel template.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/sandro/mygest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from ai_classifier.models import DocumentExtractionTemplate
from api.v1.ai_classifier.views_ai_import import DataExtractionService
import json


def test_cu_extraction():
    """Testa estrazione CU con template AI"""
    
    # File CU di test
    cu_file = '/home/sandro/mygest/testi_pdf/CU.pdf'
    
    if not os.path.exists(cu_file):
        print(f"❌ File non trovato: {cu_file}")
        return
    
    print(f"📄 File CU: {cu_file}")
    print(f"   Dimensione: {os.path.getsize(cu_file) / 1024:.1f} KB\n")
    
    # Carica template CU
    try:
        template = DocumentExtractionTemplate.objects.get(tipo_documento__codice='CU')
        print(f"✓ Template caricato: {template.nome}")
        print(f"  - Pagine: {template.numero_pagine}")
        print(f"  - Zone: {sum(p.zone.count() for p in template.pagine.all())}")
        print(f"  - Mapping: {template.mapping_campi.count()}\n")
    except DocumentExtractionTemplate.DoesNotExist:
        print("❌ Template CU non trovato")
        return
    
    # Esegui estrazione
    print("=" * 60)
    print("ESTRAZIONE DATI CON TEMPLATE AI")
    print("=" * 60 + "\n")
    
    service = DataExtractionService()
    
    try:
        result = service.extract_from_template(
            file_path=cu_file,
            template=template
        )
        
        print(f"Estrazione completa: {result['estrazione_completa']}\n")
        
        print("CAMPI ESTRATTI:")
        print("-" * 60)
        
        for campo in result['campi_estratti']:
            status = "✓" if campo['validazione_ok'] else "✗"
            print(f"\n{status} {campo['nome_campo']} ({campo['tipo_dato']})")
            print(f"   Etichetta: {campo['etichetta']}")
            print(f"   Valore: {repr(campo['valore'])}")
            
            if campo.get('confidence'):
                print(f"   Confidence: {campo['confidence']:.2%}")
            
            if not campo['validazione_ok'] and campo.get('errore_validazione'):
                print(f"   ⚠️  Errore: {campo['errore_validazione']}")
            
            # Mapping
            if campo.get('mapping'):
                m = campo['mapping']
                print(f"   → Mapping: {m['tipo_campo_destinazione']} = {m['nome_campo_destinazione']}")
                if m['funzione_trasformazione']:
                    print(f"      Trasformazione: {m['funzione_trasformazione']}")
            else:
                print(f"   ⚠️  Nessun mapping configurato")
        
        print("\n" + "=" * 60)
        print("RIEPILOGO")
        print("=" * 60)
        
        campi_ok = sum(1 for c in result['campi_estratti'] if c['validazione_ok'])
        campi_totali = len(result['campi_estratti'])
        campi_mappati = sum(1 for c in result['campi_estratti'] if c.get('mapping'))
        
        print(f"Campi validati: {campi_ok}/{campi_totali}")
        print(f"Campi mappati: {campi_mappati}/{campi_totali}")
        
        # Salva risultato completo
        output_file = '/tmp/cu_extraction_test.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Risultato completo salvato in: {output_file}")
        
    except Exception as e:
        print(f"❌ ERRORE durante estrazione:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_cu_extraction()
