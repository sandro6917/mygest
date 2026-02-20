#!/usr/bin/env python
"""
Test per verificare che il fix della bulk creation funzioni correttamente
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica

User = get_user_model()

print("=" * 70)
print("TEST FIX BULK CREATION")
print("=" * 70)

# 1. Verifica che esista una voce parent con consente_intestazione=True
print("\n1️⃣  Verifica voce parent...")
voce_parent = TitolarioVoce.objects.filter(consente_intestazione=True).first()

if not voce_parent:
    print("❌ ERRORE: Nessuna voce con consente_intestazione=True trovata")
    print("   Crea una voce con: consente_intestazione=True")
    exit(1)

print(f"✓ Voce parent trovata: {voce_parent.codice} - {voce_parent.titolo}")

# 2. Verifica anagrafiche disponibili
print("\n2️⃣  Verifica anagrafiche disponibili...")
anagrafiche_disponibili = voce_parent.get_anagrafiche_disponibili()
count = anagrafiche_disponibili.count()

if count == 0:
    print("⚠️  WARNING: Nessuna anagrafica disponibile")
    print("   Tutte le anagrafiche hanno già voci intestate")
else:
    print(f"✓ Anagrafiche disponibili: {count}")
    # Mostra prime 5
    for i, ana in enumerate(anagrafiche_disponibili[:5], 1):
        print(f"   {i}. {ana.codice} - {ana.display_name()}")
    if count > 5:
        print(f"   ... e altre {count - 5}")

# 3. Test accesso alla pagina admin (simulato)
print("\n3️⃣  Verifica template JavaScript...")

js_file_path = '/home/sandro/mygest/static/admin/js/titolario_auto_fill.js'
if os.path.exists(js_file_path):
    with open(js_file_path, 'r') as f:
        js_content = f.read()
    
    # Verifica che contenga il fix
    if 'isBulkCreationPage' in js_content:
        print("✓ Fix JavaScript presente (rilevamento pagina bulk creation)")
    else:
        print("❌ Fix JavaScript NON presente")
    
    # Verifica che non ci siano chiamate duplicate
    if js_content.count('waitForJQuery();') == 1:
        print("✓ Nessuna chiamata duplicata a waitForJQuery()")
    else:
        print(f"⚠️  Trovate {js_content.count('waitForJQuery();')} chiamate a waitForJQuery()")
else:
    print(f"❌ File JavaScript non trovato: {js_file_path}")

# 4. Verifica template bulk_creation_form.html
print("\n4️⃣  Verifica template HTML...")

template_path = '/home/sandro/mygest/templates/admin/titolario/bulk_creation_form.html'
if os.path.exists(template_path):
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Verifica elementi chiave
    checks = {
        'form.anagrafiche': 'Campo anagrafiche nel form',
        'form.crea_sottovoci': 'Checkbox crea_sottovoci',
        'select-all': 'Pulsante seleziona tutti',
        'deselect-all': 'Pulsante deseleziona tutti',
        'selection-counter': 'Contatore selezione',
    }
    
    for key, desc in checks.items():
        if key in template_content:
            print(f"✓ {desc}")
        else:
            print(f"❌ {desc} - NON TROVATO")
else:
    print(f"❌ Template non trovato: {template_path}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETATO")
print("=" * 70)
print("\n📝 NOTE:")
print("   - Il fix JavaScript previene l'inizializzazione nella pagina bulk creation")
print("   - Il JavaScript si attiverà SOLO nelle pagine add/change di singole voci")
print("   - Non dovresti più vedere errori 'Campo anagrafica non trovato' in bulk creation")
print("\n🔧 PROSSIMI PASSI:")
print("   1. Ricarica la pagina admin nel browser (Ctrl+Shift+R per hard refresh)")
print("   2. Vai in Titolario → Voci Titolario")
print("   3. Seleziona una voce con 'Consente intestazione' = Sì")
print("   4. Action: 'Crea voci intestate per anagrafiche selezionate'")
print("   5. Verifica che non ci siano più errori JavaScript nella console\n")
