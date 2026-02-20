#!/usr/bin/env python
"""
Script per creare la configurazione StampaLista per le unità fisiche dell'archivio.

Usage:
    python manage.py shell < scripts/setup_stampa_lista_unita_fisiche.py
    
Oppure:
    python scripts/setup_stampa_lista_unita_fisiche.py
"""

import os
import sys
import django

# Setup Django se eseguito come script standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
    django.setup()

from stampe.models import StampaFormato, StampaLista, StampaColonna


def setup_stampa_lista_unita_fisiche():
    """
    Crea la configurazione di base per stampare la lista dei contenuti di un'unità fisica.
    """
    
    print("🔧 Setup StampaLista per Unità Fisiche...")
    
    # 1. Crea o recupera il formato A4 Landscape
    formato, created = StampaFormato.objects.get_or_create(
        slug="a4-landscape",
        defaults={
            "nome": "A4 Orizzontale",
            "larghezza_mm": 297.0,
            "altezza_mm": 210.0,
            "orientamento": "L",
            "margine_top_mm": 10.0,
            "margine_right_mm": 10.0,
            "margine_bottom_mm": 10.0,
            "margine_left_mm": 10.0,
            "font_nome_default": "Helvetica",
            "font_size_default": 9.0,
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creato formato: {formato.nome}")
    else:
        print(f"  ℹ️  Formato esistente: {formato.nome}")
    
    # 2. Crea la StampaLista per archivio_fisico.unitafisica
    lista, created = StampaLista.objects.get_or_create(
        app_label="archivio_fisico",
        model_name="unitafisica",
        slug="archiviofisicolistastampa",
        defaults={
            "nome": "Lista Contenuti Unità Fisica",
            "formato": formato,
            "is_default": True,
            "note": "Lista degli oggetti contenuti in un'unità fisica (sottounità, fascicoli, documenti)",
            "layout": "table",
            
            # Titolo
            "titolo": "Contenuti Unità Fisica",
            "titolo_x_mm": 10.0,
            "titolo_y_mm": 10.0,
            "titolo_larghezza_mm": 277.0,
            "titolo_bold": True,
            "titolo_italic": False,
            "titolo_font_size": 14.0,
            
            # Intestazione
            "intestazione": "",
            "intestazione_x_mm": 10.0,
            "intestazione_y_mm": 25.0,
            "intestazione_font_size": 10.0,
            
            # Piè di pagina
            "piedipagina": "MyGest - Gestione Archivio Fisico",
            "piedipagina_x_mm": 10.0,
            "piedipagina_y_mm": 10.0,
            "piedipagina_font_size": 8.0,
            
            # Filtri: mostra figli dell'unità corrente
            "filter_def": {
                "parent_id": ":unita_id"
            },
            
            # Ordinamento
            "order_by": ["tipo", "ordine", "codice", "nome"],
            
            # Stile
            "header_font_name": "Helvetica-Bold",
            "header_font_size": 9.0,
            "row_font_name": "Helvetica",
            "row_font_size": 9.0,
            "row_max_lines": 2,
            "row_spacing": 1.2,
            
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creata lista: {lista.nome}")
    else:
        print(f"  ℹ️  Lista esistente: {lista.nome}")
    
    # 3. Crea le colonne per la lista
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
            "larghezza_mm": 80.0,
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
            "larghezza_mm": 20.0,
            "align": "center",
        },
    ]
    
    colonne_create = 0
    for col_config in colonne_config:
        colonna, created = StampaColonna.objects.get_or_create(
            lista=lista,
            ordine=col_config["ordine"],
            defaults={
                "tipo": col_config["tipo"],
                "label": col_config["label"],
                "attr_path": col_config["attr_path"],
                "larghezza_mm": col_config["larghezza_mm"],
                "align": col_config["align"],
                "visibile": True,
            }
        )
        
        if created:
            colonne_create += 1
    
    if colonne_create > 0:
        print(f"  ✅ Create {colonne_create} colonne")
    else:
        print(f"  ℹ️  Colonne già esistenti")
    
    print("\n✅ Setup completato!")
    print(f"\n📋 Configurazione:")
    print(f"   - Formato: {formato.nome} ({formato.larghezza_mm}x{formato.altezza_mm} mm)")
    print(f"   - Lista: {lista.nome}")
    print(f"   - Slug: {lista.slug}")
    print(f"   - Colonne: {lista.colonne.count()}")
    print(f"\n🔗 Endpoint API:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/")
    print(f"\n💡 Per personalizzare:")
    print(f"   Django Admin → Stampe → Liste di stampa → {lista.nome}")


if __name__ == "__main__":
    setup_stampa_lista_unita_fisiche()
