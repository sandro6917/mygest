#!/usr/bin/env python
"""
Completa i mapping del template AI per Certificazioni Uniche.

Aggiunge i 6 mapping mancanti per salvare tutti i campi estratti.
"""
import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.chdir(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from ai_classifier.models import DocumentExtractionTemplate, ExtractionFieldMapping


def main():
    print("=" * 60)
    print("COMPLETA MAPPING TEMPLATE CU")
    print("=" * 60 + "\n")
    
    # 1. Carica template CU
    try:
        template = DocumentExtractionTemplate.objects.get(tipo_documento__codice='CU')
        print(f"✓ Template trovato: {template.nome}")
        print(f"  - Zone definite: {sum(p.zone.count() for p in template.pagine.all())}")
        print(f"  - Mapping attuali: {template.mapping_campi.count()}\n")
    except DocumentExtractionTemplate.DoesNotExist:
        print("❌ Template CU non trovato!")
        return
    
    # 2. Definisci nuovi mapping
    nuovi_mapping = [
        {
            'nome_campo_template': 'anno_imposta',
            'tipo_campo_destinazione': 'attribute',
            'nome_campo_destinazione': 'anno_riferimento',
            'descrizione': 'Anno fiscale di riferimento della CU'
        },
        {
            'nome_campo_template': 'anno_presentazione',
            'tipo_campo_destinazione': 'attribute',
            'nome_campo_destinazione': 'anno_presentazione',
            'descrizione': 'Anno di presentazione della CU'
        },
        {
            'nome_campo_template': 'denominazione_datore',
            'tipo_campo_destinazione': 'field',
            'nome_campo_destinazione': 'cliente.anagrafica.denominazione',
            'descrizione': 'Denominazione/Ragione sociale del datore (PG)'
        },
        {
            'nome_campo_template': 'nome_datore',
            'tipo_campo_destinazione': 'field',
            'nome_campo_destinazione': 'cliente.anagrafica.nome',
            'descrizione': 'Nome del datore di lavoro (PF)'
        },
        {
            'nome_campo_template': 'cognome_lavoratore',
            'tipo_campo_destinazione': 'attribute',
            'nome_campo_destinazione': 'dipendente_cognome',
            'descrizione': 'Cognome del lavoratore dipendente'
        },
        {
            'nome_campo_template': 'nome_lavoratore',
            'tipo_campo_destinazione': 'attribute',
            'nome_campo_destinazione': 'dipendente_nome',
            'descrizione': 'Nome del lavoratore dipendente'
        },
    ]
    
    # 3. Crea mapping
    print("CREAZIONE NUOVI MAPPING:")
    print("-" * 60 + "\n")
    
    creati = 0
    esistenti = 0
    
    for mapping_data in nuovi_mapping:
        nome_campo = mapping_data['nome_campo_template']
        
        # Verifica se esiste già
        mapping_esistente = template.mapping_campi.filter(
            nome_campo_template=nome_campo
        ).first()
        
        if mapping_esistente:
            print(f"⚠️  {nome_campo}")
            print(f"   Già mappato su: {mapping_esistente.nome_campo_destinazione}")
            print()
            esistenti += 1
            continue
        
        # Crea nuovo mapping
        mapping = ExtractionFieldMapping.objects.create(
            template=template,
            nome_campo_template=mapping_data['nome_campo_template'],
            tipo_campo_destinazione=mapping_data['tipo_campo_destinazione'],
            nome_campo_destinazione=mapping_data['nome_campo_destinazione']
        )
        
        print(f"✓ {nome_campo}")
        print(f"  → {mapping.tipo_campo_destinazione}: {mapping.nome_campo_destinazione}")
        print(f"  Descrizione: {mapping_data['descrizione']}")
        print()
        
        creati += 1
    
    # 4. Riepilogo
    print("=" * 60)
    print("RIEPILOGO")
    print("=" * 60)
    print(f"Mapping creati: {creati}")
    print(f"Mapping già esistenti: {esistenti}")
    print(f"Mapping totali: {template.mapping_campi.count()}")
    print()
    
    # 5. Mostra tutti i mapping correnti
    print("MAPPING COMPLETI:")
    print("-" * 60)
    for m in template.mapping_campi.all().order_by('nome_campo_template'):
        print(f"{m.nome_campo_template}")
        print(f"  → {m.tipo_campo_destinazione}: {m.nome_campo_destinazione}")
    print()
    
    # 6. Verifica completezza
    zone_totali = set()
    for pag in template.pagine.all():
        for zona in pag.zone.all():
            zone_totali.add(zona.nome_campo)
    
    zone_mappate = set(template.mapping_campi.values_list('nome_campo_template', flat=True))
    zone_non_mappate = zone_totali - zone_mappate
    
    if zone_non_mappate:
        print("⚠️  ZONE ANCORA SENZA MAPPING:")
        for zona in sorted(zone_non_mappate):
            print(f"  - {zona}")
        print()
    else:
        print("✓ Tutti i campi del template hanno un mapping!")
        print()
    
    print(f"Copertura: {len(zone_mappate)}/{len(zone_totali)} campi mappati")
    print(f"Percentuale: {len(zone_mappate)/len(zone_totali)*100:.0f}%")
    print()
    
    if creati > 0:
        print("✓ Configurazione completata con successo!")
        print()
        print("PROSSIMI STEP:")
        print("1. Modificare CertificazioniUnicheImporter per usare DataExtractionService")
        print("2. Implementare logica creazione Anagrafica/Cliente automatica")
        print("3. Testare importazione CU con template AI")
        print()
        print("Vedi: /home/sandro/mygest/docs/ANALISI_ESTRAZIONE_CU_AI.md")


if __name__ == '__main__':
    main()
