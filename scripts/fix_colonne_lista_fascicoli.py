#!/usr/bin/env python
"""
Script per correggere le colonne della lista fascicoli.

Usage:
    source venv/bin/activate
    python scripts/fix_colonne_lista_fascicoli.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaLista, StampaColonna


def fix_colonne_fascicoli():
    """
    Corregge gli attr_path delle colonne della lista fascicoli
    """
    
    print("🔧 Correzione Colonne Lista Fascicoli...")
    
    # Trova la StampaLista
    try:
        lista = StampaLista.objects.get(
            app_label="fascicoli",
            model_name="fascicolo",
            slug="LST_FASCICOLI_UBICAZIONE"
        )
        print(f"  ✅ Trovata lista: {lista.nome}")
    except StampaLista.DoesNotExist:
        print("  ❌ StampaLista non trovata!")
        return
    
    # Definizione colonne CORRETTE
    colonne_config = [
        {
            "ordine": 1,
            "tipo": "text",
            "label": "Codice",
            "attr_path": "codice",
            "larghezza_mm": 35.0,
            "align": "left",
        },
        {
            "ordine": 2,
            "tipo": "text",
            "label": "Titolo",
            "attr_path": "titolo",
            "larghezza_mm": 80.0,
            "align": "left",
        },
        {
            "ordine": 3,
            "tipo": "text",
            "label": "Anno",
            "attr_path": "anno",
            "larghezza_mm": 20.0,
            "align": "center",
        },
        {
            "ordine": 4,
            "tipo": "text",
            "label": "Cliente",
            "attr_path": "cliente.anagrafica.ragione_sociale",  # CORRETTO
            "larghezza_mm": 65.0,
            "align": "left",
        },
        {
            "ordine": 5,
            "tipo": "text",
            "label": "Titolario",
            "attr_path": "titolario_voce.codice_completo",  # CORRETTO: era titolario.codice_completo
            "larghezza_mm": 40.0,
            "align": "left",
        },
        {
            "ordine": 6,
            "tipo": "text",
            "label": "Stato",
            "attr_path": "stato",
            "larghezza_mm": 25.0,
            "align": "center",
        },
    ]
    
    # Elimina colonne esistenti
    count_delete = lista.colonne.count()
    if count_delete > 0:
        lista.colonne.all().delete()
        print(f"  🗑️  Eliminate {count_delete} colonne esistenti")
    
    # Crea le nuove colonne
    for col_config in colonne_config:
        colonna = StampaColonna.objects.create(
            lista=lista,
            ordine=col_config["ordine"],
            tipo=col_config["tipo"],
            label=col_config["label"],
            attr_path=col_config["attr_path"],
            larghezza_mm=col_config["larghezza_mm"],
            align=col_config["align"],
            visibile=True,
        )
        print(f"  ✅ Creata colonna: {colonna.label} → {colonna.attr_path}")
    
    print(f"\n✅ Correzione completata!")
    print(f"   - Lista: {lista.nome}")
    print(f"   - Colonne: {lista.colonne.count()}")
    print(f"\n🔗 Test endpoint:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/?lista=LST_FASCICOLI_UBICAZIONE")


if __name__ == "__main__":
    fix_colonne_fascicoli()
