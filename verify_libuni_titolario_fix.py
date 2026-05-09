#!/usr/bin/env python
"""
Script di verifica per fix titolario LIBUNI

Verifica che:
1. Esista voce titolario con codice 'LIBUNI'
2. La funzione importa_zip_come_libro_unico ora cerchi correttamente LIBUNI
3. Non ci siano riferimenti residui a HR-PAY nel flusso Libro Unico

Uso:
    python manage.py shell < verify_libuni_titolario_fix.py
"""

from titolario.models import TitolarioVoce
from documenti.models import DocumentiTipo
import inspect

print("\n" + "="*80)
print("VERIFICA FIX TITOLARIO LIBUNI")
print("="*80 + "\n")

# 1. Verifica esistenza voce titolario LIBUNI
print("1. VERIFICA VOCE TITOLARIO LIBUNI")
print("-" * 80)

voce_libuni = TitolarioVoce.objects.filter(codice='LIBUNI').first()

if voce_libuni:
    print(f"✅ Voce titolario LIBUNI trovata:")
    print(f"   ID: {voce_libuni.id}")
    print(f"   Codice: {voce_libuni.codice}")
    print(f"   Titolo: {voce_libuni.titolo}")
    print(f"   Parent: {voce_libuni.parent.codice if voce_libuni.parent else 'Nessuno'}")
    if voce_libuni.pattern_codice:
        print(f"   Pattern codice: {voce_libuni.pattern_codice}")
else:
    print("⚠️  ATTENZIONE: Voce titolario LIBUNI non trovata!")
    print("   È necessario creare la voce titolario LIBUNI prima di usare la funzione.")
    print("\n   Esempio creazione:")
    print("   ```python")
    print("   from titolario.models import TitolarioVoce")
    print("   ")
    print("   # Trova parent HR-PAY")
    print("   hr_pay = TitolarioVoce.objects.filter(codice='HR-PAY').first()")
    print("   ")
    print("   # Crea voce LIBUNI")
    print("   libuni = TitolarioVoce.objects.create(")
    print("       codice='LIBUNI',")
    print("       titolo='Libro Unico',")
    print("       parent=hr_pay,  # o None se voce di primo livello")
    print("       pattern_codice='{CLI}-LIBUNI-{ANNO}-{SEQ:03d}'")
    print("   )")
    print("   ```")

print()

# 2. Verifica tipo documento LIBUNI
print("2. VERIFICA TIPO DOCUMENTO LIBUNI")
print("-" * 80)

try:
    tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
    print(f"✅ Tipo documento LIBUNI trovato:")
    print(f"   ID: {tipo_libuni.id}")
    print(f"   Codice: {tipo_libuni.codice}")
    print(f"   Nome: {tipo_libuni.nome}")
    if tipo_libuni.nome_file_pattern:
        print(f"   Pattern nome file: {tipo_libuni.nome_file_pattern}")
except DocumentiTipo.DoesNotExist:
    print("❌ ERRORE: Tipo documento LIBUNI non trovato!")

print()

# 3. Verifica funzione non cerchi più HR-PAY
print("3. VERIFICA CODICE FUNZIONE importa_zip_come_libro_unico")
print("-" * 80)

try:
    from api.v1.documenti.importa_libro_unico import importa_zip_come_libro_unico
    
    # Ottieni il codice sorgente
    source = inspect.getsource(importa_zip_come_libro_unico)
    
    # Verifica che non contenga riferimenti a HR-PAY
    if 'HR-PAY' in source or 'HRPAY' in source or 'titolario_hrpay' in source:
        print("❌ ERRORE: La funzione contiene ancora riferimenti a HR-PAY!")
        # Mostra le linee problematiche
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if 'HR-PAY' in line or 'HRPAY' in line or 'titolario_hrpay' in line:
                print(f"   Linea {i}: {line.strip()}")
    else:
        print("✅ La funzione non contiene più riferimenti a HR-PAY")
    
    # Verifica che contenga riferimenti a LIBUNI
    if 'titolario_libuni' in source and "codice='LIBUNI'" in source:
        print("✅ La funzione cerca correttamente il titolario LIBUNI")
    else:
        print("⚠️  ATTENZIONE: La funzione potrebbe non cercare correttamente LIBUNI")
        
except Exception as e:
    print(f"❌ ERRORE: {e}")

print()

# 4. Riepilogo
print("="*80)
print("RIEPILOGO")
print("="*80)

if voce_libuni and tipo_libuni:
    print("✅ Prerequisiti soddisfatti:")
    print("   - Voce titolario LIBUNI esiste")
    print("   - Tipo documento LIBUNI configurato")
    print("\n🎯 Il fix dovrebbe funzionare correttamente!")
    print("\nPROSSIMI PASSI:")
    print("1. Testare importazione ZIP come Libro Unico")
    print("2. Verificare che il documento creato abbia titolario LIBUNI")
    print("3. Controllare path del file salvato")
else:
    print("⚠️  ATTENZIONE: Prerequisiti mancanti")
    if not voce_libuni:
        print("   - Creare voce titolario LIBUNI")
    if not tipo_libuni:
        print("   - Configurare tipo documento LIBUNI")

print()
