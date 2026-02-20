#!/usr/bin/env python
"""
Script per creare StampaLista per contenitori mobili (archivio_fisso=False)

Usage:
    source venv/bin/activate
    python scripts/setup_lista_contenitori.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaFormato, StampaLista, StampaColonna


def setup_lista_contenitori():
    """
    Crea StampaLista per elencare contenitori mobili (archivio_fisso=False)
    """
    
    print("🔧 Setup Lista Contenitori Mobili...")
    
    # Trova formato A4 Orizzontale
    try:
        formato = StampaFormato.objects.get(slug="a4-landscape")
        print(f"  ℹ️  Formato: {formato.nome}")
    except StampaFormato.DoesNotExist:
        print("  ❌ Formato A4 Orizzontale non trovato!")
        return
    
    # Crea o aggiorna StampaLista
    lista, created = StampaLista.objects.update_or_create(
        app_label="archivio_fisico",
        model_name="unitafisica",
        slug="LST_CONTENITORI",
        defaults={
            "nome": "Elenco Contenitori Mobili",
            "formato": formato,
            "layout": "tree",  # Layout ad albero
            "filter_def": {"archivio_fisso": False},  # Solo contenitori mobili
            "tree_root_filter": {"parent_id": ":unita_id"},  # Figli diretti dell'unità come radici
            "tree_parent_field": "parent",
            "tree_children_attr": "figli",
            "tree_indent_mm": 6.0,  # Indentazione per livello
            "order_by": ["ordine", "nome"],
            "attivo": True,
        }
    )
    
    action = "creata" if created else "aggiornata"
    print(f"  ℹ️  Lista {action}: {lista.nome}")
    
    # Elimina colonne esistenti
    if not created:
        StampaColonna.objects.filter(lista=lista).delete()
        print("  🗑️  Colonne precedenti eliminate")
    
    # Definizione colonne
    colonne_config = [
        {
            "ordine": 1,
            "tipo": "text",
            "label": "Codice",
            "attr_path": "codice",
            "larghezza_mm": 30.0,
            "align": "left",
        },
        {
            "ordine": 2,
            "tipo": "text",
            "label": "Nome",
            "attr_path": "nome",
            "larghezza_mm": 60.0,
            "align": "left",
        },
        {
            "ordine": 3,
            "tipo": "text",
            "label": "Tipo",
            "attr_path": "tipo_display",
            "larghezza_mm": 35.0,
            "align": "left",
        },
        {
            "ordine": 4,
            "tipo": "text",
            "label": "Percorso Completo",
            "attr_path": "full_path",
            "larghezza_mm": 90.0,
            "align": "left",
        },
        {
            "ordine": 5,
            "tipo": "text",
            "label": "Contenuta In",
            "attr_path": "contenuta_in.nome",
            "larghezza_mm": 50.0,
            "align": "left",
        },
        {
            "ordine": 6,
            "tipo": "text",
            "label": "Descrizione",
            "attr_path": "descrizione",
            "larghezza_mm": 50.0,
            "align": "left",
        },
    ]
    
    # Crea le colonne
    for col_config in colonne_config:
        StampaColonna.objects.create(
            lista=lista,
            **col_config
        )
    
    print(f"  ✅ Creati {len(colonne_config)} campi")
    
    print("\n✅ Setup completato!\n")
    print("📋 Lista creata:")
    print(f"   - Nome: {lista.nome}")
    print(f"   - Slug: {lista.slug}")
    print(f"   - Formato: {formato.nome}")
    print(f"   - Filtro: archivio_fisso=False")
    print(f"   - Colonne: {len(colonne_config)}")
    print("\n🔗 Endpoint API:")
    print("   GET /api/v1/archivio-fisico/unita/{id}/stampa_lista_contenuti/?tipo=LST_CONTENITORI")
    print("\n💡 Mostra solo:")
    print("   - Contenitori (archivio_fisso=False)")
    print("   - Cartelline")
    print("   - Fascicoli mobili")
    print("   - Altre unità non fisse")


if __name__ == "__main__":
    setup_lista_contenitori()
