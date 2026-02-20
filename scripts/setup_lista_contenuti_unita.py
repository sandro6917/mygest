#!/usr/bin/env python
"""
Script per creare una lista di stampa che elenca fascicoli e documenti contenuti in un'unità fisica.

Usage:
    source venv/bin/activate
    python scripts/setup_lista_contenuti_unita.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaFormato, StampaLista, StampaColonna


def setup_lista_contenuti():
    """
    Crea una lista per stampare fascicoli e documenti contenuti in un'unità fisica.
    
    Questa lista mostrerà:
    - Fascicoli archiviati nell'unità fisica
    - Documenti archiviati nell'unità fisica
    """
    
    print("🔧 Setup Lista Contenuti Unità Fisica (Fascicoli + Documenti)...")
    
    # 1. Recupera o crea il formato A4 Landscape
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
    
    # 2. LISTA PER FASCICOLI
    lista_fascicoli, created = StampaLista.objects.get_or_create(
        app_label="fascicoli",
        model_name="fascicolo",
        slug="LST_FASCICOLI_UBICAZIONE",
        defaults={
            "nome": "Fascicoli per Ubicazione",
            "formato": formato,
            "is_default": False,
            "note": "Elenco fascicoli contenuti in un'unità fisica dell'archivio",
            "layout": "table",
            
            # Titolo
            "titolo": "Fascicoli Archiviati",
            "titolo_x_mm": 10.0,
            "titolo_y_mm": 10.0,
            "titolo_larghezza_mm": 277.0,
            "titolo_bold": True,
            "titolo_font_size": 14.0,
            
            # Piè di pagina
            "piedipagina": "MyGest - Gestione Archivio Fisico",
            "piedipagina_x_mm": 10.0,
            "piedipagina_y_mm": 10.0,
            "piedipagina_font_size": 8.0,
            
            # Filtri: fascicoli con questa ubicazione
            "filter_def": {
                "ubicazione_id": ":unita_id"
            },
            
            # Ordinamento
            "order_by": ["codice", "anno"],
            
            # Stile
            "header_font_name": "Helvetica-Bold",
            "header_font_size": 9.0,
            "row_font_name": "Helvetica",
            "row_font_size": 8.0,
            "row_max_lines": 2,
            "row_spacing": 1.2,
            
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creata lista fascicoli: {lista_fascicoli.nome}")
    else:
        print(f"  ℹ️  Lista fascicoli esistente: {lista_fascicoli.nome}")
    
    # Colonne per fascicoli
    if created or lista_fascicoli.colonne.count() == 0:
        colonne_fascicoli = [
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
                "larghezza_mm": 90.0,
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
                "attr_path": "cliente.anagrafica.ragione_sociale",
                "larghezza_mm": 70.0,
                "align": "left",
            },
            {
                "ordine": 5,
                "tipo": "text",
                "label": "Titolario",
                "attr_path": "titolario.codice_completo",
                "larghezza_mm": 40.0,
                "align": "left",
            },
            {
                "ordine": 6,
                "tipo": "text",
                "label": "Stato",
                "attr_path": "stato",
                "larghezza_mm": 22.0,
                "align": "center",
            },
        ]
        
        lista_fascicoli.colonne.all().delete()
        for col_config in colonne_fascicoli:
            StampaColonna.objects.create(
                lista=lista_fascicoli,
                ordine=col_config["ordine"],
                tipo=col_config["tipo"],
                label=col_config["label"],
                attr_path=col_config["attr_path"],
                larghezza_mm=col_config["larghezza_mm"],
                align=col_config["align"],
                visibile=True,
            )
        print(f"  ✅ Create {len(colonne_fascicoli)} colonne per fascicoli")
    
    # 3. LISTA PER DOCUMENTI
    lista_documenti, created = StampaLista.objects.get_or_create(
        app_label="documenti",
        model_name="documento",
        slug="LST_DOCUMENTI_UBICAZIONE",
        defaults={
            "nome": "Documenti per Ubicazione",
            "formato": formato,
            "is_default": False,
            "note": "Elenco documenti contenuti in un'unità fisica dell'archivio",
            "layout": "table",
            
            # Titolo
            "titolo": "Documenti Archiviati",
            "titolo_x_mm": 10.0,
            "titolo_y_mm": 10.0,
            "titolo_larghezza_mm": 277.0,
            "titolo_bold": True,
            "titolo_font_size": 14.0,
            
            # Piè di pagina
            "piedipagina": "MyGest - Gestione Archivio Fisico",
            "piedipagina_x_mm": 10.0,
            "piedipagina_y_mm": 10.0,
            "piedipagina_font_size": 8.0,
            
            # Filtri: documenti con questa ubicazione, solo cartacei
            "filter_def": {
                "ubicazione_id": ":unita_id",
                "digitale": False
            },
            
            # Ordinamento
            "order_by": ["codice", "data_documento"],
            
            # Stile
            "header_font_name": "Helvetica-Bold",
            "header_font_size": 9.0,
            "row_font_name": "Helvetica",
            "row_font_size": 8.0,
            "row_max_lines": 2,
            "row_spacing": 1.2,
            
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creata lista documenti: {lista_documenti.nome}")
    else:
        print(f"  ℹ️  Lista documenti esistente: {lista_documenti.nome}")
    
    # Colonne per documenti
    if created or lista_documenti.colonne.count() == 0:
        colonne_documenti = [
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
                "label": "Descrizione",
                "attr_path": "descrizione",
                "larghezza_mm": 80.0,
                "align": "left",
            },
            {
                "ordine": 3,
                "tipo": "text",
                "label": "Tipo",
                "attr_path": "tipo.nome",
                "larghezza_mm": 30.0,
                "align": "left",
            },
            {
                "ordine": 4,
                "tipo": "text",
                "label": "Data",
                "attr_path": "data_documento",
                "larghezza_mm": 25.0,
                "align": "center",
            },
            {
                "ordine": 5,
                "tipo": "text",
                "label": "Cliente",
                "attr_path": "cliente.anagrafica.ragione_sociale",
                "larghezza_mm": 60.0,
                "align": "left",
            },
            {
                "ordine": 6,
                "tipo": "text",
                "label": "Fascicolo",
                "attr_path": "fascicolo.codice",
                "larghezza_mm": 30.0,
                "align": "left",
            },
            {
                "ordine": 7,
                "tipo": "text",
                "label": "Stato",
                "attr_path": "stato",
                "larghezza_mm": 17.0,
                "align": "center",
            },
        ]
        
        lista_documenti.colonne.all().delete()
        for col_config in colonne_documenti:
            StampaColonna.objects.create(
                lista=lista_documenti,
                ordine=col_config["ordine"],
                tipo=col_config["tipo"],
                label=col_config["label"],
                attr_path=col_config["attr_path"],
                larghezza_mm=col_config["larghezza_mm"],
                align=col_config["align"],
                visibile=True,
            )
        print(f"  ✅ Create {len(colonne_documenti)} colonne per documenti")
    
    print("\n✅ Setup completato!")
    print(f"\n📋 Liste create:")
    print(f"   1. {lista_fascicoli.nome} (slug: {lista_fascicoli.slug})")
    print(f"      - Colonne: {lista_fascicoli.colonne.count()}")
    print(f"   2. {lista_documenti.nome} (slug: {lista_documenti.slug})")
    print(f"      - Colonne: {lista_documenti.colonne.count()}")
    print(f"\n🔗 Come usare:")
    print(f"   - Per stampare fascicoli:")
    print(f"     GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/?lista=LST_FASCICOLI_UBICAZIONE")
    print(f"   - Per stampare documenti:")
    print(f"     GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/?lista=LST_DOCUMENTI_UBICAZIONE")
    print(f"\n💡 Personalizza in Django Admin → Stampe → Liste di stampa")


if __name__ == "__main__":
    setup_lista_contenuti()
