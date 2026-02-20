#!/usr/bin/env python
"""
Script per creare una configurazione di stampa "Copertina A4" per unità fisiche.

Usage:
    source venv/bin/activate
    python scripts/setup_copertina_unita.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaFormato, StampaModulo, StampaCampo


def setup_copertina_unita():
    """
    Crea una configurazione per stampare la copertina A4 di un'unità fisica.
    La copertina mostra il codice e il nome dell'unità al centro orizzontalmente
    e ad 1/3 in verticale della pagina.
    """
    
    print("🔧 Setup Copertina A4 Unità Fisica...")
    
    # 1. Recupera il formato A4 Portrait (verticale)
    formato = StampaFormato.objects.get(slug="A4")
    print(f"  ℹ️  Formato: {formato.nome}")
    
    # Dimensioni A4 Portrait: 210mm x 297mm
    # 1/3 verticale = 297 / 3 = 99mm dall'alto = 198mm dal basso
    
    # 2. Crea il modulo per copertina
    modulo, created = StampaModulo.objects.get_or_create(
        app_label="archivio_fisico",
        model_name="unitafisica",
        slug="COPERTINA_UNITA",
        defaults={
            "nome": "Copertina Unità Fisica",
            "formato": formato,
            "is_default": False,
            "note": "Copertina A4 per identificare unità fisiche con codice e nome evidenziati al centro",
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creato modulo: {modulo.nome}")
    else:
        print(f"  ℹ️  Modulo esistente: {modulo.nome}")
    
    # 3. Elimina campi esistenti e ricrea
    modulo.campi.all().delete()
    
    # Campi della copertina - Layout migliorato e professionale
    # MARGINI: Bordo principale a x=5, y=5 (margini di 5mm)
    campi_config = [
        # === INTESTAZIONE ===
        
        # LOGO/TITOLO AZIENDA (in alto a sinistra)
        {
            "ordine": 1,
            "tipo": "static",
            "static_value": "MyGest - Gestione Archivio",
            "x_mm": 10.0,
            "y_mm": 10.0,
            "font_size": 11.0,
            "bold": True,
        },
        
        # DATA STAMPA (in alto a destra)
        {
            "ordine": 2,
            "tipo": "template",
            "template": "Stampato: {now}",
            "x_mm": 195.0,
            "y_mm": 10.0,
            "font_size": 8.0,
            "align": "right",
        },
        
        # PATH COMPLETO (sotto il logo, più grande)
        {
            "ordine": 3,
            "tipo": "attr",
            "attr_path": "full_path",
            "x_mm": 10.0,
            "y_mm": 20.0,
            "font_size": 10.0,
            "bold": True,
        },
        
        # === BORDO E SEPARATORI ===
        
        # BORDO PRINCIPALE (x=5, y=5)
        {
            "ordine": 4,
            "tipo": "shape",
            "shape_kind": "rect",
            "x_mm": 5.0,
            "y_mm": 5.0,
            "shape_width_mm": 200.0,  # 210 - 10 (margini totali)
            "shape_height_mm": 287.0,  # 297 - 10
            "border_width_pt": 2.0,
            "border_color": "black",
        },
        
        # LINEA SOTTO INTESTAZIONE
        {
            "ordine": 5,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 10.0,
            "y_mm": 30.0,
            "shape_width_mm": 190.0,
            "border_width_pt": 1.5,
            "border_color": "black",
        },
        
        # === SEZIONE PRINCIPALE - CODICE E NOME (CENTRATA) ===
        
        # BOX EVIDENZIATO PER CODICE (sfondo)
        {
            "ordine": 6,
            "tipo": "shape",
            "shape_kind": "rounded_rect",
            "x_mm": 50.0,
            "y_mm": 85.0,
            "shape_width_mm": 110.0,
            "shape_height_mm": 50.0,
            "border_width_pt": 2.0,
            "border_color": "black",
            "corner_radius_mm": 5.0,
        },
        
        # ETICHETTA "CODICE UNITÀ"
        {
            "ordine": 7,
            "tipo": "static",
            "static_value": "CODICE UNITÀ",
            "x_mm": 105.0,
            "y_mm": 90.0,
            "font_size": 10.0,
            "bold": True,
            "align": "center",
        },
        
        # CODICE (molto grande)
        {
            "ordine": 8,
            "tipo": "attr",
            "attr_path": "codice",
            "x_mm": 105.0,
            "y_mm": 110.0,
            "font_size": 72.0,
            "bold": True,
            "align": "center",
        },
        
        # NOME (grande, sotto il codice)
        {
            "ordine": 9,
            "tipo": "attr",
            "attr_path": "nome",
            "x_mm": 105.0,
            "y_mm": 150.0,
            "font_size": 36.0,
            "bold": False,
            "align": "center",
        },
        
        # LINEA SEPARATRICE ELEGANTE
        {
            "ordine": 10,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 35.0,
            "y_mm": 165.0,
            "shape_width_mm": 140.0,
            "border_width_pt": 1.0,
            "border_color": "darkgray",
        },
        
        # === SEZIONE DETTAGLI (2 COLONNE) ===
        
        # COLONNA SINISTRA - TIPO
        {
            "ordine": 11,
            "tipo": "static",
            "static_value": "TIPO:",
            "x_mm": 20.0,
            "y_mm": 180.0,
            "font_size": 9.0,
            "bold": True,
        },
        
        {
            "ordine": 12,
            "tipo": "attr",
            "attr_path": "tipo_display",
            "x_mm": 20.0,
            "y_mm": 187.0,
            "font_size": 12.0,
            "bold": True,
        },
        
        # COLONNA DESTRA - STATO ARCHIVIO
        {
            "ordine": 13,
            "tipo": "static",
            "static_value": "ARCHIVIO:",
            "x_mm": 115.0,
            "y_mm": 180.0,
            "font_size": 9.0,
            "bold": True,
        },
        
        {
            "ordine": 14,
            "tipo": "template",
            "template": "{obj.archivio_fisso}",
            "x_mm": 115.0,
            "y_mm": 187.0,
            "font_size": 12.0,
            "bold": True,
        },
        
        # LINEA SEPARATRICE
        {
            "ordine": 15,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 15.0,
            "y_mm": 200.0,
            "shape_width_mm": 180.0,
            "border_width_pt": 0.5,
            "border_color": "lightgray",
        },
        
        # CONTENUTA IN (se presente)
        {
            "ordine": 16,
            "tipo": "template",
            "template": "Contenuta in: {obj.parent}",
            "x_mm": 20.0,
            "y_mm": 210.0,
            "font_size": 10.0,
            "larghezza_mm": 170.0,
        },
        
        # DESCRIZIONE
        {
            "ordine": 17,
            "tipo": "attr",
            "attr_path": "descrizione",
            "label": "Descrizione:",
            "x_mm": 20.0,
            "y_mm": 222.0,
            "larghezza_mm": 170.0,
            "font_size": 9.0,
            "max_lines": 3,
        },
        
        # NOTE
        {
            "ordine": 18,
            "tipo": "attr",
            "attr_path": "note",
            "label": "Note:",
            "x_mm": 20.0,
            "y_mm": 240.0,
            "larghezza_mm": 170.0,
            "font_size": 8.0,
            "max_lines": 2,
        },
        
        # === DATI TECNICI (PICCOLI, IN BASSO) ===
        
        # LINEA SEPARATRICE FOOTER
        {
            "ordine": 19,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 10.0,
            "y_mm": 255.0,
            "shape_width_mm": 190.0,
            "border_width_pt": 1.0,
            "border_color": "gray",
        },
        
        # Progressivo e Ordine (sulla stessa riga)
        {
            "ordine": 20,
            "tipo": "template",
            "template": "Prog: {obj.progressivo} | Ord: {obj.ordine}",
            "x_mm": 10.0,
            "y_mm": 262.0,
            "font_size": 7.0,
        },
        
        # DATA CREAZIONE
        {
            "ordine": 21,
            "tipo": "attr",
            "attr_path": "created_at",
            "label": "Creato:",
            "x_mm": 10.0,
            "y_mm": 268.0,
            "font_size": 7.0,
        },
        
        # ULTIMA MODIFICA (centro)
        {
            "ordine": 22,
            "tipo": "attr",
            "attr_path": "updated_at",
            "label": "Agg.:",
            "x_mm": 80.0,
            "y_mm": 268.0,
            "font_size": 7.0,
        },
        
        # ID DATABASE (destra)
        {
            "ordine": 23,
            "tipo": "attr",
            "attr_path": "id",
            "label": "ID:",
            "x_mm": 200.0,
            "y_mm": 268.0,
            "font_size": 7.0,
            "align": "right",
        },
        
        # STATO ATTIVO (indicatore)
        {
            "ordine": 24,
            "tipo": "attr",
            "attr_path": "attivo",
            "label": "Attivo:",
            "x_mm": 10.0,
            "y_mm": 274.0,
            "font_size": 7.0,
        },
    ]
    
    for campo_def in campi_config:
        StampaCampo.objects.create(modulo=modulo, **campo_def)
    
    print(f"  ✅ Creati {len(campi_config)} campi")
    
    print("\n✅ Setup completato!")
    print(f"\n📋 Copertina creata:")
    print(f"   - Nome: {modulo.nome}")
    print(f"   - Slug: {modulo.slug}")
    print(f"   - Formato: A4 Verticale")
    print(f"   - Campi: {modulo.campi.count()}")
    print(f"\n🔗 Endpoint API:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_copertina/")
    print(f"\n💡 Caratteristiche:")
    print(f"   - Codice e nome al centro (1/3 dall'alto)")
    print(f"   - Path completo in alto")
    print(f"   - Tipo e info in basso")
    print(f"   - Bordo decorativo")


if __name__ == "__main__":
    setup_copertina_unita()

