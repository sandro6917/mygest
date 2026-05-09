#!/usr/bin/env python
"""
Script per verificare e creare gli attributi dinamici per il tipo documento LIBUNI
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo, AttributoDefinizione

def check_and_create_libuni_attributes():
    """Verifica e crea gli attributi per LIBUNI se necessario"""
    
    # Cerca il tipo documento LIBUNI
    try:
        tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
        print(f"✓ Tipo documento LIBUNI trovato: {tipo_libuni.nome}")
    except DocumentiTipo.DoesNotExist:
        print("✗ Tipo documento LIBUNI non trovato!")
        print("  Devi prima creare il tipo documento LIBUNI nel sistema.")
        return False
    
    # Definizione degli attributi necessari
    attributi_necessari = [
        {
            'codice': 'periodo',
            'nome': 'Periodo',
            'tipo_dato': 'text',
            'widget': 'text',
            'required': False,
            'ordine': 1,
            'help_text': 'Periodo di riferimento (es: Aprile 2025)'
        },
        {
            'codice': 'anno',
            'nome': 'Anno',
            'tipo_dato': 'int',
            'widget': 'number',
            'required': False,
            'ordine': 2,
            'help_text': 'Anno di riferimento'
        },
        {
            'codice': 'mese',
            'nome': 'Mese',
            'tipo_dato': 'int',
            'widget': 'number',
            'required': False,
            'ordine': 3,
            'help_text': 'Mese di riferimento (1-12)'
        },
        {
            'codice': 'num_cedolini',
            'nome': 'Numero Cedolini',
            'tipo_dato': 'int',
            'widget': 'number',
            'required': False,
            'ordine': 4,
            'help_text': 'Numero di cedolini contenuti nello ZIP'
        },
    ]
    
    print(f"\nVerifica degli attributi per {tipo_libuni.codice}:")
    print("-" * 60)
    
    created_count = 0
    updated_count = 0
    
    for attr_data in attributi_necessari:
        codice = attr_data['codice']
        
        # Cerca se esiste già
        attr_def = AttributoDefinizione.objects.filter(
            tipo_documento=tipo_libuni,
            codice=codice
        ).first()
        
        if attr_def:
            print(f"✓ Attributo '{codice}' già esistente")
            # Opzionalmente aggiorna i campi
            updated = False
            if attr_def.nome != attr_data['nome']:
                attr_def.nome = attr_data['nome']
                updated = True
            if attr_def.help_text != attr_data['help_text']:
                attr_def.help_text = attr_data['help_text']
                updated = True
            
            if updated:
                attr_def.save()
                updated_count += 1
                print(f"  → Aggiornato")
        else:
            # Crea nuovo attributo
            attr_def = AttributoDefinizione.objects.create(
                tipo_documento=tipo_libuni,
                **attr_data
            )
            created_count += 1
            print(f"✓ Attributo '{codice}' creato")
    
    print("-" * 60)
    print(f"\nRiepilogo:")
    print(f"  Attributi creati:    {created_count}")
    print(f"  Attributi aggiornati: {updated_count}")
    print(f"  Attributi totali:     {AttributoDefinizione.objects.filter(tipo_documento=tipo_libuni).count()}")
    print("\n✓ Verifica completata!")
    
    return True

if __name__ == '__main__':
    check_and_create_libuni_attributes()
