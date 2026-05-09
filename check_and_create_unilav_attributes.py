#!/usr/bin/env python
"""
Script per verificare e creare gli attributi UNILAV mancanti.

Questo script controlla quali attributi sono estratti dal parser UNILAV
e li crea automaticamente nel database se non esistono.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo, AttributoDefinizione

# Definizione completa attributi UNILAV estratti dal parser
ATTRIBUTI_UNILAV = {
    # Documento
    'codice_comunicazione': {'nome': 'Codice Comunicazione', 'tipo_dato': 'string', 'required': True},
    'tipo': {'nome': 'Tipo Comunicazione', 'tipo_dato': 'choice', 'required': True, 
             'choices': 'Assunzione|Assunzione a termine|Assunzione a tempo indeterminato|Proroga|Trasformazione|Cessazione'},
    'modello': {'nome': 'Modello', 'tipo_dato': 'string', 'required': False},
    'data_comunicazione': {'nome': 'Data Comunicazione', 'tipo_dato': 'date', 'required': True},
    
    # Datore
    'datore_cf': {'nome': 'Datore - Codice Fiscale', 'tipo_dato': 'string', 'required': True},
    'datore_denominazione': {'nome': 'Datore - Denominazione', 'tipo_dato': 'string', 'required': True},
    'datore_email': {'nome': 'Datore - Email', 'tipo_dato': 'string', 'required': False},
    'datore_telefono': {'nome': 'Datore - Telefono', 'tipo_dato': 'string', 'required': False},
    'datore_comune': {'nome': 'Datore - Comune', 'tipo_dato': 'string', 'required': False},
    'datore_cap': {'nome': 'Datore - CAP', 'tipo_dato': 'string', 'required': False},
    'datore_indirizzo': {'nome': 'Datore - Indirizzo', 'tipo_dato': 'string', 'required': False},
    
    # Lavoratore
    'lavoratore_cf': {'nome': 'Lavoratore - Codice Fiscale', 'tipo_dato': 'string', 'required': True},
    'lavoratore_cognome': {'nome': 'Lavoratore - Cognome', 'tipo_dato': 'string', 'required': True},
    'lavoratore_nome': {'nome': 'Lavoratore - Nome', 'tipo_dato': 'string', 'required': True},
    'lavoratore_sesso': {'nome': 'Lavoratore - Sesso', 'tipo_dato': 'choice', 'required': False, 'choices': 'M|F'},
    'lavoratore_data_nascita': {'nome': 'Lavoratore - Data di Nascita', 'tipo_dato': 'date', 'required': False},
    'lavoratore_comune_nascita': {'nome': 'Lavoratore - Comune di Nascita', 'tipo_dato': 'string', 'required': False},
    'lavoratore_comune': {'nome': 'Lavoratore - Comune Domicilio', 'tipo_dato': 'string', 'required': False},
    'lavoratore_cap': {'nome': 'Lavoratore - CAP Domicilio', 'tipo_dato': 'string', 'required': False},
    'lavoratore_indirizzo': {'nome': 'Lavoratore - Indirizzo Domicilio', 'tipo_dato': 'string', 'required': False},
    
    # Rapporto di lavoro
    'data_inizio_rapporto': {'nome': 'Data Inizio Rapporto', 'tipo_dato': 'date', 'required': False},
    'data_fine_rapporto': {'nome': 'Data Fine Rapporto', 'tipo_dato': 'date', 'required': False},
    'data_proroga': {'nome': 'Data Fine Proroga', 'tipo_dato': 'date', 'required': False},
    'data_trasformazione': {'nome': 'Data Trasformazione', 'tipo_dato': 'date', 'required': False},
    'causa_trasformazione': {'nome': 'Causa Trasformazione', 'tipo_dato': 'string', 'required': False},
    'centro_impiego': {'nome': 'Centro per l\'Impiego', 'tipo_dato': 'string', 'required': False},
    'provincia_impiego': {'nome': 'Provincia Impiego', 'tipo_dato': 'string', 'required': False},
    
    # Dati previdenziali e contrattuali
    'ente_previdenziale': {'nome': 'Ente Previdenziale', 'tipo_dato': 'string', 'required': False},
    'codice_ente_previdenziale': {'nome': 'Codice Ente Previdenziale', 'tipo_dato': 'string', 'required': False},
    'pat_inail': {'nome': 'PAT INAIL', 'tipo_dato': 'string', 'required': False},
    'tipologia_contrattuale': {'nome': 'Tipologia Contrattuale', 'tipo_dato': 'string', 'required': False},
    'tipo_orario': {'nome': 'Tipo Orario', 'tipo_dato': 'string', 'required': False},
    'ore_settimanali': {'nome': 'Ore Settimanali', 'tipo_dato': 'string', 'required': False},
    'qualifica': {'nome': 'Qualifica Professionale', 'tipo_dato': 'string', 'required': False},
    'contratto_collettivo': {'nome': 'Contratto Collettivo', 'tipo_dato': 'string', 'required': False},
    'livello': {'nome': 'Livello di Inquadramento', 'tipo_dato': 'string', 'required': False},
    'retribuzione': {'nome': 'Retribuzione/Compenso', 'tipo_dato': 'string', 'required': False},
}


def main():
    print("=" * 80)
    print("VERIFICA E CREAZIONE ATTRIBUTI UNILAV")
    print("=" * 80)
    
    try:
        tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
        print(f"\n✅ Tipo documento UNILAV trovato: {tipo_unilav.nome}")
    except DocumentiTipo.DoesNotExist:
        print("\n❌ ERRORE: Tipo documento UNILAV non trovato!")
        print("   Creare il tipo documento 'UNILAV' in Django Admin prima di eseguire questo script.")
        return
    
    # Verifica attributi esistenti
    attributi_esistenti = {
        attr.codice: attr 
        for attr in AttributoDefinizione.objects.filter(tipo_documento=tipo_unilav)
    }
    
    print(f"\n📋 Attributi esistenti: {len(attributi_esistenti)}")
    print(f"📋 Attributi definiti: {len(ATTRIBUTI_UNILAV)}")
    print(f"📋 Attributi da creare: {len(ATTRIBUTI_UNILAV) - len(attributi_esistenti)}")
    
    # Crea attributi mancanti
    creati = 0
    aggiornati = 0
    
    for codice, config in ATTRIBUTI_UNILAV.items():
        if codice in attributi_esistenti:
            # Attributo esiste, eventualmente aggiorna
            attr = attributi_esistenti[codice]
            
            # Aggiorna solo se ci sono differenze significative
            update_needed = False
            if attr.nome != config['nome']:
                attr.nome = config['nome']
                update_needed = True
            if attr.tipo_dato != config['tipo_dato']:
                attr.tipo_dato = config['tipo_dato']
                update_needed = True
            if attr.required != config['required']:
                attr.required = config['required']
                update_needed = True
            if config.get('choices') and attr.choices != config['choices']:
                attr.choices = config['choices']
                update_needed = True
            
            if update_needed:
                attr.save()
                aggiornati += 1
                print(f"  🔄 Aggiornato: {codice}")
        else:
            # Crea nuovo attributo
            AttributoDefinizione.objects.create(
                tipo_documento=tipo_unilav,
                codice=codice,
                nome=config['nome'],
                tipo_dato=config['tipo_dato'],
                required=config['required'],
                choices=config.get('choices', ''),
                widget=config.get('widget', ''),
                ordine=list(ATTRIBUTI_UNILAV.keys()).index(codice) + 1,
            )
            creati += 1
            print(f"  ✅ Creato: {codice} - {config['nome']}")
    
    print(f"\n{'=' * 80}")
    print(f"✅ Completato!")
    print(f"   • Attributi creati: {creati}")
    print(f"   • Attributi aggiornati: {aggiornati}")
    print(f"   • Attributi totali: {AttributoDefinizione.objects.filter(tipo_documento=tipo_unilav).count()}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
