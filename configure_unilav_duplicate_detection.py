#!/usr/bin/env python
"""
Script per configurare il rilevamento duplicati per il tipo documento UNILAV.

Configurazione:
- Chiave univoca: codice_comunicazione (obbligatorio per UNILAV)
- Scope: cliente (stesso datore di lavoro)
- Strategy: exact_match (codice comunicazione deve essere identico)

Esecuzione:
    python manage.py shell < configure_unilav_duplicate_detection.py
    
    # oppure
    source venv/bin/activate
    python configure_unilav_duplicate_detection.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo
import json

def configure_unilav_duplicate_detection():
    """
    Configura il rilevamento duplicati per UNILAV basato su codice_comunicazione.
    """
    print("🔍 Ricerca tipo documento UNILAV...")
    
    unilav = DocumentiTipo.objects.filter(codice='UNILAV').first()
    
    if not unilav:
        print("❌ Tipo documento UNILAV non trovato!")
        print("   Crealo prima con:")
        print("   DocumentiTipo.objects.create(codice='UNILAV', nome='UNILAV', descrizione='Comunicazione UNILAV')")
        return
    
    print(f"✅ UNILAV trovato (ID: {unilav.id}, Nome: {unilav.nome})")
    
    # Configurazione duplicate detection per UNILAV
    # Basato su codice_comunicazione come chiave univoca
    duplicate_config = {
        "enabled": True,
        "strategy": "exact_match",
        "scope": {
            "cliente": True,      # Verifica duplicati per stesso cliente (datore)
            "anno": False,        # Non limitare per anno (codice_comunicazione è già univoco)
            "fascicolo": False    # Non limitare per fascicolo
        },
        "fields": [
            {
                "type": "attribute",
                "code": "codice_comunicazione",
                "required": True,     # Codice comunicazione è OBBLIGATORIO per UNILAV
                "weight": 1.0,
                "normalize": True,    # Normalizza (trim, uppercase)
                "case_sensitive": False
            },
            {
                "type": "attribute",
                "code": "data_comunicazione",
                "required": False,    # Data comunicazione è secondaria
                "weight": 0.5,        # Peso minore rispetto a codice
                "normalize": True
            }
        ],
        "match_mode": "all_required_or_any_weighted",  # Richiede codice_comunicazione
        "min_confidence": 0.9  # Confidenza minima 90% per considerare duplicato
    }
    
    print("\n📋 Configurazione duplicate detection:")
    print(json.dumps(duplicate_config, indent=2))
    
    # Salva configurazione
    print("\n💾 Salvataggio configurazione...")
    unilav.duplicate_detection_config = duplicate_config
    unilav.save()
    
    print("✅ Configurazione salvata con successo!")
    
    # Verifica
    print("\n🔍 Verifica configurazione salvata...")
    unilav.refresh_from_db()
    print(json.dumps(unilav.duplicate_detection_config, indent=2))
    
    print("\n✨ Configurazione completata!")
    print("   Il sistema ora rileverà duplicati UNILAV basati su:")
    print("   - codice_comunicazione (chiave primaria)")
    print("   - cliente (stesso datore di lavoro)")
    print("   - data_comunicazione (peso secondario)")

if __name__ == '__main__':
    configure_unilav_duplicate_detection()
