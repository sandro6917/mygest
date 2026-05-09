#!/usr/bin/env python
"""
Script per verificare/creare AttributoDefinizione per tipo documento BPAG (Busta Paga/Cedolino).

Questo script:
1. Verifica che il tipo documento BPAG (Busta Paga) esista
2. Crea/aggiorna le AttributoDefinizione necessarie per i cedolini:
   - anno_riferimento (int): Anno di riferimento
   - mese_riferimento (int): Mese di riferimento
   - mensilita (string): Mensilità
   - dipendente (string): Nome completo dipendente
   - numero_cedolino (string): Numero cedolino (per rilevamento duplicati)
   - data_ora_cedolino (string): Data/Ora cedolino (per rilevamento duplicati)

Uso:
    python check_and_create_cedol_attributes.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo, AttributoDefinizione


def main():
    """Verifica/crea attributi per tipo documento BPAG"""
    
    print("=" * 70)
    print("VERIFICA/CREAZIONE ATTRIBUTI PER TIPO DOCUMENTO BPAG")
    print("=" * 70)
    print()
    
    # 1. Verifica tipo documento BPAG
    print("[1] Verifica tipo documento BPAG...")
    try:
        tipo_cedol = DocumentiTipo.objects.get(codice='BPAG')
        print(f"    ✓ Tipo documento BPAG trovato: {tipo_cedol.nome} (ID: {tipo_cedol.id})")
    except DocumentiTipo.DoesNotExist:
        print("    ✗ ERRORE: Tipo documento BPAG non trovato!")
        print("      Creare manualmente il tipo documento con codice 'BPAG'")
        sys.exit(1)
    
    print()
    
    # 2. Definizioni attributi da creare
    attributi = [
        {
            'codice': 'anno_riferimento',
            'nome': 'Anno riferimento',
            'tipo_dato': 'int',
            'required': False,
        },
        {
            'codice': 'mese_riferimento',
            'nome': 'Mese riferimento',
            'tipo_dato': 'int',
            'required': False,
        },
        {
            'codice': 'mensilita',
            'nome': 'Mensilità',
            'tipo_dato': 'string',
            'required': False,
        },
        {
            'codice': 'dipendente',
            'nome': 'Dipendente',
            'tipo_dato': 'string',
            'required': False,
        },
        {
            'codice': 'numero_cedolino',
            'nome': 'Numero cedolino',
            'tipo_dato': 'string',
            'required': False,
        },
        {
            'codice': 'data_ora_cedolino',
            'nome': 'Data/Ora cedolino',
            'tipo_dato': 'string',
            'required': False,
        },
    ]
    
    print(f"[2] Verifica/crea {len(attributi)} attributi...")
    print()
    
    for attr in attributi:
        codice = attr['codice']
        
        # Get or create
        definizione, created = AttributoDefinizione.objects.get_or_create(
            tipo_documento=tipo_cedol,
            codice=codice,
            defaults={
                'nome': attr['nome'],
                'tipo_dato': attr['tipo_dato'],
                'required': attr['required'],
            }
        )
        
        if created:
            print(f"    ✓ Attributo '{codice}' creato")
            print(f"      - Nome: {attr['nome']}")
            print(f"      - Tipo: {attr['tipo_dato']}")
            print(f"      - Obbligatorio: {attr['required']}")
        else:
            # Aggiorna se necessario
            updated = False
            if definizione.nome != attr['nome']:
                definizione.nome = attr['nome']
                updated = True
            if definizione.tipo_dato != attr['tipo_dato']:
                definizione.tipo_dato = attr['tipo_dato']
                updated = True
            if definizione.required != attr['required']:
                definizione.required = attr['required']
                updated = True
            
            if updated:
                definizione.save()
                print(f"    ✓ Attributo '{codice}' già esistente → Aggiornato")
            else:
                print(f"    ✓ Attributo '{codice}' già esistente e corretto")
        
        print()
    
    print("=" * 70)
    print("COMPLETATO")
    print("=" * 70)
    print()
    
    # Riepilogo finale
    print("Attributi BPAG configurati:")
    for attr_def in AttributoDefinizione.objects.filter(tipo_documento=tipo_cedol).order_by('codice'):
        print(f"  - {attr_def.codice}: {attr_def.nome} ({attr_def.tipo_dato})")
    
    print()


if __name__ == '__main__':
    main()
