#!/usr/bin/env python
"""
Script per configurare le colonne della StampaLista "LST_OBJ" per le unità fisiche.

Usage:
    source venv/bin/activate
    python scripts/setup_colonne_lista_unita.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaLista, StampaColonna


def setup_colonne():
    """
    Configura le colonne per la lista LST_OBJ (Elenco oggetti unità fisica)
    """
    
    print("🔧 Setup Colonne per Lista Unità Fisica...")
    
    # Trova la StampaLista
    try:
        lista = StampaLista.objects.get(
            app_label="archivio_fisico",
            model_name="unitafisica",
            slug="LST_OBJ"
        )
        print(f"  ✅ Trovata lista: {lista.nome}")
    except StampaLista.DoesNotExist:
        print("  ❌ StampaLista non trovata!")
        print("  ℹ️  Verifica che Model name sia 'unitafisica' (non 'archiviofisicolistastampa')")
        return
    
    # Definizione colonne
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
            "label": "Nome",
            "attr_path": "nome",
            "larghezza_mm": 70.0,
            "align": "left",
        },
        {
            "ordine": 3,
            "tipo": "text",
            "label": "Tipo",
            "attr_path": "tipo_display",
            "larghezza_mm": 40.0,
            "align": "left",
        },
        {
            "ordine": 4,
            "tipo": "text",
            "label": "Percorso",
            "attr_path": "full_path",
            "larghezza_mm": 100.0,
            "align": "left",
        },
        {
            "ordine": 5,
            "tipo": "text",
            "label": "Attivo",
            "attr_path": "attivo",
            "larghezza_mm": 25.0,
            "align": "center",
        },
        {
            "ordine": 6,
            "tipo": "text",
            "label": "Archivio Fisso",
            "attr_path": "archivio_fisso",
            "larghezza_mm": 25.0,
            "align": "center",
        },
    ]
    
    # Elimina colonne esistenti se presenti
    count_delete = lista.colonne.count()
    if count_delete > 0:
        lista.colonne.all().delete()
        print(f"  🗑️  Eliminate {count_delete} colonne esistenti")
    
    # Crea le nuove colonne
    colonne_create = 0
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
        colonne_create += 1
        print(f"  ✅ Creata colonna: {colonna.label} ({colonna.attr_path})")
    
    print(f"\n✅ Setup completato!")
    print(f"   - Lista: {lista.nome}")
    print(f"   - Colonne create: {colonne_create}")
    print(f"\n🔗 Test endpoint:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/")
    print(f"\n💡 Personalizza:")
    print(f"   Django Admin → Stampe → Liste di stampa → {lista.nome} → Colonne")


if __name__ == "__main__":
    setup_colonne()
