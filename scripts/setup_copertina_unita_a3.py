#!/usr/bin/env python
"""
Script per creare una configurazione di stampa "Copertina A3 Orizzontale" per unità fisiche.
Duplica i campi di COPERTINA_UNITA traslando quelli con x >= 170mm più a destra.

Usage:
    source venv/bin/activate
    python scripts/setup_copertina_unita_a3.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from stampe.models import StampaFormato, StampaModulo, StampaCampo


def setup_copertina_unita_a3():
    """
    Crea una configurazione per stampare la copertina A3 ORIZZONTALE di un'unità fisica.
    Duplica i campi del modulo COPERTINA_UNITA traslando i campi con x >= 170mm.
    """
    
    print("🔧 Setup Copertina A3 Orizzontale Unità Fisica...")
    
    # 1. Recupera il formato A3 esistente (slug "Copertina")
    try:
        formato = StampaFormato.objects.get(slug="Copertina")
        print(f"  ℹ️  Formato esistente: {formato.nome} ({formato.larghezza_mm}x{formato.altezza_mm}mm)")
    except StampaFormato.DoesNotExist:
        print("  ❌ Formato A3 'Copertina' non trovato!")
        return
    
    # Dimensioni A3 Landscape: 420mm x 297mm
    
    # 2. Crea/Sovrascrivi il modulo per copertina A3
    modulo, created = StampaModulo.objects.update_or_create(
        app_label="archivio_fisico",
        model_name="unitafisica",
        slug="COPERTINA_UNITA_A3",
        defaults={
            "nome": "Copertina Unità Fisica A3 Orizzontale",
            "formato": formato,
            "is_default": False,
            "note": "Copertina A3 orizzontale per identificare unità fisiche - campi traslati da x=170mm in poi",
            "attivo": True,
        }
    )
    
    if created:
        print(f"  ✅ Creato modulo: {modulo.nome}")
    else:
        print(f"  ♻️  Sovrascritto modulo: {modulo.nome}")
    
    # 3. Elimina campi esistenti e ricrea
    modulo.campi.all().delete()
    
    # Campi della copertina A3 - Duplicati da COPERTINA_UNITA
    # con traslazione dei campi x >= 170mm
    # TRASLAZIONE: da A4 210mm a A3 420mm = +210mm di spazio
    # Campi con x >= 170 vengono spostati di +210mm per centrarli meglio nell'area extra
    
    TRASLAZIONE_X = 210.0  # Millimetri da aggiungere ai campi >= 170mm
    
    campi_config = [
        # === INTESTAZIONE ===
        
        # LOGO/TITOLO AZIENDA (in alto a sinistra) - NON TRASLATO
        {
            "ordine": 1,
            "tipo": "static",
            "static_value": "MyGest - Gestione Archivio",
            "x_mm": 10.0,
            "y_mm": 10.0,
            "font_size": 11.0,
            "bold": True,
        },
        
        # DATA STAMPA (in alto a destra) - TRASLATO (x=195 >= 170)
        {
            "ordine": 2,
            "tipo": "template",
            "template": "Stampato: {now}",
            "x_mm": 195.0 + TRASLAZIONE_X,
            "y_mm": 10.0,
            "font_size": 8.0,
            "align": "right",
        },
        
        # PATH COMPLETO (sotto il logo, più grande) - NON TRASLATO
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
        
        # BORDO PRINCIPALE - ADATTATO AL FORMATO A3
        {
            "ordine": 4,
            "tipo": "shape",
            "shape_kind": "rect",
            "x_mm": 5.0,
            "y_mm": 5.0,
            "shape_width_mm": 410.0,  # 420 - 10 (margini totali)
            "shape_height_mm": 287.0,  # 297 - 10
            "border_width_pt": 2.0,
            "border_color": "black",
        },
        
        # LINEA SOTTO INTESTAZIONE - ADATTATA
        {
            "ordine": 5,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 10.0,
            "y_mm": 30.0,
            "shape_width_mm": 400.0,  # Estesa per A3
            "border_width_pt": 1.5,
            "border_color": "black",
        },
        
        # === SEZIONE PRINCIPALE - CODICE E NOME (CENTRATA) ===
        
        # BOX EVIDENZIATO PER CODICE (sfondo) - NON TRASLATO (centrato)
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
        
        # ETICHETTA "CODICE UNITÀ" - NON TRASLATO
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
        
        # CODICE (molto grande) - NON TRASLATO
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
        
        # NOME (grande, sotto il codice) - NON TRASLATO
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
        
        # LINEA SEPARATRICE ELEGANTE - NON TRASLATO
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
        
        # COLONNA SINISTRA - TIPO - TRASLATO (x=20 < 170, ma spostiamolo per bilanciare)
        # Lasciamo i dettagli nella loro posizione originale (< 170mm)
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
        
        # COLONNA DESTRA - STATO ARCHIVIO - NON TRASLATO (< 170)
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
        
        # LINEA SEPARATRICE - TRASLATO (x=15 < 170, ma width può estendersi)
        # Lasciamo x fisso ma estendiamo la larghezza
        {
            "ordine": 15,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 15.0,
            "y_mm": 200.0,
            "shape_width_mm": 390.0,  # Estesa per A3
            "border_width_pt": 0.5,
            "border_color": "lightgray",
        },
        
        # CONTENUTA IN (se presente) - NON TRASLATO (< 170)
        # Larghezza aumentata per utilizzare lo spazio A3
        {
            "ordine": 16,
            "tipo": "template",
            "template": "Contenuta in: {obj.parent}",
            "x_mm": 20.0,
            "y_mm": 210.0,
            "font_size": 10.0,
            "larghezza_mm": 380.0,  # Estesa
        },
        
        # DESCRIZIONE - TRASLATO (larghezza era 170 >= soglia)
        # Aumentiamo la larghezza per sfruttare A3
        {
            "ordine": 17,
            "tipo": "attr",
            "attr_path": "descrizione",
            "label": "Descrizione:",
            "x_mm": 20.0,
            "y_mm": 222.0,
            "larghezza_mm": 380.0,  # Estesa
            "font_size": 9.0,
            "max_lines": 3,
        },
        
        # NOTE - TRASLATO (larghezza era 170 >= soglia)
        {
            "ordine": 18,
            "tipo": "attr",
            "attr_path": "note",
            "label": "Note:",
            "x_mm": 20.0,
            "y_mm": 240.0,
            "larghezza_mm": 380.0,  # Estesa
            "font_size": 8.0,
            "max_lines": 2,
        },
        
        # === DATI TECNICI (PICCOLI, IN BASSO) ===
        
        # LINEA SEPARATRICE FOOTER - ESTESA
        {
            "ordine": 19,
            "tipo": "shape",
            "shape_kind": "line",
            "x_mm": 10.0,
            "y_mm": 255.0,
            "shape_width_mm": 400.0,  # Estesa per A3
            "border_width_pt": 1.0,
            "border_color": "gray",
        },
        
        # Progressivo e Ordine (sulla stessa riga) - NON TRASLATO
        {
            "ordine": 20,
            "tipo": "template",
            "template": "Prog: {obj.progressivo} | Ord: {obj.ordine}",
            "x_mm": 10.0,
            "y_mm": 262.0,
            "font_size": 7.0,
        },
        
        # DATA CREAZIONE - NON TRASLATO
        {
            "ordine": 21,
            "tipo": "attr",
            "attr_path": "created_at",
            "label": "Creato:",
            "x_mm": 10.0,
            "y_mm": 268.0,
            "font_size": 7.0,
        },
        
        # ULTIMA MODIFICA (centro) - NON TRASLATO (< 170)
        {
            "ordine": 22,
            "tipo": "attr",
            "attr_path": "updated_at",
            "label": "Agg.:",
            "x_mm": 80.0,
            "y_mm": 268.0,
            "font_size": 7.0,
        },
        
        # ID DATABASE (destra) - TRASLATO (x=200 >= 170)
        {
            "ordine": 23,
            "tipo": "attr",
            "attr_path": "id",
            "label": "ID:",
            "x_mm": 200.0 + TRASLAZIONE_X,
            "y_mm": 268.0,
            "font_size": 7.0,
            "align": "right",
        },
        
        # STATO ATTIVO (indicatore) - NON TRASLATO
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
    print(f"\n📋 Copertina A3 creata:")
    print(f"   - Nome: {modulo.nome}")
    print(f"   - Slug: {modulo.slug}")
    print(f"   - Formato: A3 Orizzontale (420x297 mm)")
    print(f"   - Campi: {modulo.campi.count()}")
    print(f"   - Traslazione applicata: +{TRASLAZIONE_X}mm ai campi x >= 170mm")
    print(f"\n🔗 Endpoint API:")
    print(f"   GET /api/v1/archivio-fisico/unita/{{id}}/stampa_copertina/?modulo=COPERTINA_UNITA_A3")
    print(f"\n💡 Caratteristiche:")
    print(f"   - Duplicato da COPERTINA_UNITA")
    print(f"   - Formato A3 orizzontale")
    print(f"   - Campi con x >= 170mm traslati di +210mm")
    print(f"   - Coordinate Y mantenute identiche")


if __name__ == "__main__":
    setup_copertina_unita_a3()
