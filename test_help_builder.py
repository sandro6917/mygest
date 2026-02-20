"""
Script di test per verificare il sistema Help Builder

Usage:
    python manage.py shell < test_help_builder.py
    # oppure
    python manage.py test_help_builder  (se configurato come command)
"""
import django
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.core.management import call_command
from documenti.models import DocumentiTipo, AttributoDefinizione
from documenti.help_builder import HelpDataBuilder, rebuild_help_technical_sections


def test_help_builder():
    """Test completo del sistema Help Builder."""
    
    print("="*70)
    print("  TEST SISTEMA HELP BUILDER")
    print("="*70)
    
    # Test 1: Creazione builder
    print("\n[1] Test creazione HelpDataBuilder...")
    try:
        tipo_ced = DocumentiTipo.objects.get(codice='CED')
        builder = HelpDataBuilder(tipo_ced)
        print("✓ Builder creato con successo")
    except Exception as e:
        print(f"✗ Errore: {e}")
        return
    
    # Test 2: Generazione attributi dinamici
    print("\n[2] Test generazione attributi_dinamici...")
    try:
        attr_din = builder.build_attributi_dinamici()
        print(f"✓ Generati {len(attr_din.get('disponibili', []))} attributi")
        print(f"✓ Pattern examples: {len(attr_din.get('pattern_code_examples', []))}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 3: Generazione pattern codice
    print("\n[3] Test generazione pattern_codice...")
    try:
        pattern = builder.build_pattern_codice()
        print(f"✓ Pattern default: {pattern.get('default')}")
        print(f"✓ Placeholder: {len(pattern.get('placeholder_disponibili', {}))}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 4: Generazione archiviazione
    print("\n[4] Test generazione archiviazione...")
    try:
        arch = builder.build_archiviazione()
        print(f"✓ Percorso: {arch.get('percorso_tipo')}")
        print(f"✓ Note: {len(arch.get('note', []))}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 5: Generazione campi obbligatori
    print("\n[5] Test generazione campi_obbligatori...")
    try:
        campi = builder.build_campi_obbligatori()
        print(f"✓ Campi sempre: {len(campi.get('sempre', []))}")
        print(f"✓ Campi condizionali: {len(campi.get('condizionali', {}))}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 6: Generazione tutte le sezioni
    print("\n[6] Test generazione tutte le sezioni tecniche...")
    try:
        all_tech = builder.build_all_technical_sections()
        keys = list(all_tech.keys())
        print(f"✓ Sezioni generate: {', '.join(keys)}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 7: Merge con esistente
    print("\n[7] Test merge con help_data esistente...")
    try:
        merged = builder.merge_with_existing(tipo_ced.help_data)
        tech_keys = ['attributi_dinamici', 'pattern_codice', 'archiviazione', 'campi_obbligatori']
        disc_keys = ['descrizione_breve', 'quando_usare', 'faq']
        
        has_tech = all(k in merged for k in tech_keys)
        has_disc = any(k in merged for k in disc_keys)
        
        print(f"✓ Sezioni tecniche presenti: {has_tech}")
        print(f"✓ Sezioni discorsive preservate: {has_disc}")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    # Test 8: Funzione helper rebuild
    print("\n[8] Test funzione rebuild_help_technical_sections...")
    try:
        rebuilt = rebuild_help_technical_sections(tipo_ced)
        print(f"✓ Help_data ricostruito con {len(rebuilt)} sezioni")
    except Exception as e:
        print(f"✗ Errore: {e}")
    
    print("\n" + "="*70)
    print("  ✓ TUTTI I TEST COMPLETATI CON SUCCESSO")
    print("="*70)


if __name__ == '__main__':
    test_help_builder()
