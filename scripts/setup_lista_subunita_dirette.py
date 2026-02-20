#!/usr/bin/env python
"""
Script per creare una lista di stampa che mostra solo le sottounità dirette (1 livello).

Usage:
    source venv/bin/activate
    python scripts/setup_lista_subunita_dirette.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaFormato, StampaLista, StampaColonna


def setup_lista_subunita_dirette():
    """
    Crea una lista per stampare solo le sottounità dirette (figli di primo livello).
    """
    
    print("🔧 Setup Lista Sottounità Dirette (1 livello)...")
    
    # 1. Recupera il formato A4 Landscape
    formato = StampaFormato.objects.get(slug="a4-landscape")
    print(f"  ℹ️  Formato: {formato.nome}")
    
    # 2. Crea la lista per sottounità dirette
    lista, created = StampaLista.objects.get_or_create(
        app_label="archivio_fisico",
        model_name="unitafisica",
        slug="LST_SUBUNITA_DIRETTE",
        defaults={
            "nome": "Sottounità Dirette",
            "formato": formato,
            "is_default": False,
            "note": "Elenco delle sottounità direttamente collegate (solo 1 livello)",
            "layout": "table",  # Layout tabella, non tree
            
            # Titolo
            "titolo": "",
            "titolo_template": "Sottounità (Archivio Fisso) di {unita.full_path}",
            "titolo_x_mm": 10.0,
            "titolo_y_mm": 10.0,
            "titolo_larghezza_mm": 277.0,
            "titolo_bold": True,
            "titolo_font_size": 14.0,
            
            # Piè di pagina
            "piedipagina": "MyGest - Gestione Archivio Fisico - Stampato il {now}",
            "piedipagina_x_mm": 10.0,
            "piedipagina_y_mm": 10.0,
            "piedipagina_font_size": 8.0,
            
            # FILTRO: solo figli diretti con archivio_fisso=True
            "filter_def": {
                "parent_id": ":unita_id",  # Solo figli diretti
                "archivio_fisso": True      # Solo archivio fisso
            },
            
            # Ordinamento
            "order_by": ["ordine", "tipo", "codice", "nome"],
            
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
        # Aggiorna i campi anche se esiste
        lista.titolo_template = "Sottounità (Archivio Fisso) di {unita.full_path}"
        lista.piedipagina = "MyGest - Gestione Archivio Fisico - Stampato il {now}"
        lista.filter_def = {"parent_id": ":unita_id", "archivio_fisso": True}
        lista.order_by = ["ordine", "tipo", "codice", "nome"]
        lista.save()
        print(f"  ✅ Aggiornata configurazione")
    
    # 3. Crea le colonne
    if created or lista.colonne.count() == 0:
        colonne_config = [
            {
                "ordine": 1,
                "tipo": "text",
                "label": "Ordine",
                "attr_path": "ordine",
                "larghezza_mm": 20.0,
                "align": "center",
            },
            {
                "ordine": 2,
                "tipo": "text",
                "label": "Codice",
                "attr_path": "codice",
                "larghezza_mm": 35.0,
                "align": "left",
            },
            {
                "ordine": 3,
                "tipo": "text",
                "label": "Nome",
                "attr_path": "nome",
                "larghezza_mm": 90.0,
                "align": "left",
            },
            {
                "ordine": 4,
                "tipo": "text",
                "label": "Tipo",
                "attr_path": "tipo_display",
                "larghezza_mm": 40.0,
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
            {
                "ordine": 6,
                "tipo": "text",
                "label": "Arch. Fisso",
                "attr_path": "archivio_fisso",
                "larghezza_mm": 25.0,
                "align": "center",
            },
            {
                "ordine": 7,
                "tipo": "text",
                "label": "Note",
                "attr_path": "note",
                "larghezza_mm": 47.0,
                "align": "left",
            },
        ]
        
        lista.colonne.all().delete()
        for col_config in colonne_config:
            StampaColonna.objects.create(
                lista=lista,
                ordine=col_config["ordine"],
                tipo=col_config["tipo"],
                label=col_config["label"],
                attr_path=col_config["attr_path"],
                larghezza_mm=col_config["larghezza_mm"],
                align=col_config["align"],
                visibile=True,
            )
        print(f"  ✅ Create {len(colonne_config)} colonne")
    
    print("\n✅ Setup completato!")
    print(f"\n📋 Lista creata:")
    print(f"   - Nome: {lista.nome}")
    print(f"   - Slug: {lista.slug}")
    print(f"   - Layout: {lista.layout} (tabella)")
    print(f"   - Filtro: parent_id = :unita_id AND archivio_fisso = True")
    print(f"   - Colonne: {lista.colonne.count()}")
    print(f"\n🔗 Endpoint API:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_lista_contenuti/?lista=LST_SUBUNITA_DIRETTE")
    print(f"\n💡 Caratteristiche:")
    print(f"   - Mostra solo figli diretti (1 livello)")
    print(f"   - Solo unità con archivio_fisso=True")
    print(f"   - Titolo include il path completo del padre (es. UFF/U01/ST/01)")
    print(f"   - Piè di pagina con data/ora stampa")


if __name__ == "__main__":
    setup_lista_subunita_dirette()
