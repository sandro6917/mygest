#!/usr/bin/env python
"""
Test rapido per verificare la generazione della copertina A3.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from archivio_fisico.models import UnitaFisica
from stampe.services import render_modulo_pdf, get_modulo_or_404

def test_copertina_a3():
    print("🧪 Test generazione Copertina A3...\n")
    
    # Prendi la prima unità fisica
    unita = UnitaFisica.objects.first()
    if not unita:
        print("❌ Nessuna unità fisica trovata nel database")
        return
    
    print(f"📦 Unità fisica: {unita.codice} - {unita.nome} (ID: {unita.id})")
    
    # Carica il modulo
    try:
        modulo = get_modulo_or_404(
            app_label="archivio_fisico",
            model="unitafisica",
            slug="COPERTINA_UNITA_A3"
        )
        print(f"✅ Modulo caricato: {modulo.nome}")
        print(f"   Formato: {modulo.formato.nome} ({modulo.formato.larghezza_mm}x{modulo.formato.altezza_mm}mm)")
    except Exception as e:
        print(f"❌ Errore caricamento modulo: {e}")
        return
    
    # Genera il PDF
    try:
        print("\n🔄 Generazione PDF in corso...")
        pdf_bytes = render_modulo_pdf(unita, modulo)
        
        # Salva il PDF di test
        output_path = f"/tmp/test_copertina_a3_{unita.id}.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✅ PDF generato con successo!")
        print(f"   Dimensione: {len(pdf_bytes)} bytes")
        print(f"   Salvato in: {output_path}")
        print(f"\n💡 Apri il file con: xdg-open {output_path}")
        
    except Exception as e:
        print(f"❌ Errore generazione PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_copertina_a3()
