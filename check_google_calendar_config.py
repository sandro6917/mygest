#!/usr/bin/env python
"""
Script per verificare la configurazione di Google Calendar.
Uso: python check_google_calendar_config.py
"""
import os
import sys
import json
from pathlib import Path

# Aggiungi il path del progetto Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from django.conf import settings
from scadenze.models import ScadenzaOccorrenza


def check_config():
    """Verifica la configurazione di Google Calendar"""
    print("=" * 60)
    print("VERIFICA CONFIGURAZIONE GOOGLE CALENDAR")
    print("=" * 60)
    print()
    
    # 1. Verifica il path del file credenziali
    creds_file = getattr(settings, 'GOOGLE_CALENDAR_CREDENTIALS_FILE', None)
    print(f"📁 File credenziali: {creds_file}")
    
    if not creds_file:
        print("   ✗ ERRORE: GOOGLE_CALENDAR_CREDENTIALS_FILE non configurato")
        print("   Aggiungi questa configurazione in settings_local.py")
        return False
    
    # 2. Verifica che il file esista
    if not os.path.exists(creds_file):
        print(f"   ✗ ERRORE: File non trovato!")
        print(f"   Crea il file in: {creds_file}")
        print()
        print("   Passaggi:")
        print("   1. Vai su Google Cloud Console")
        print("   2. Crea un Service Account")
        print("   3. Scarica le credenziali JSON")
        print(f"   4. Copia il file in: {creds_file}")
        return False
    
    print("   ✓ File trovato")
    
    # 3. Verifica che il file sia leggibile e valido
    try:
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
        
        # Verifica i campi essenziali
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [f for f in required_fields if f not in creds_data]
        
        if missing_fields:
            print(f"   ✗ ERRORE: Campi mancanti nel JSON: {', '.join(missing_fields)}")
            return False
        
        print("   ✓ File JSON valido")
        print(f"   Service Account: {creds_data.get('client_email')}")
        
    except json.JSONDecodeError:
        print("   ✗ ERRORE: File JSON non valido o corrotto")
        return False
    except Exception as e:
        print(f"   ✗ ERRORE: Impossibile leggere il file: {e}")
        return False
    
    print()
    
    # 4. Verifica il Calendar ID
    calendar_id = getattr(settings, 'GOOGLE_CALENDAR_DEFAULT_ID', None)
    print(f"📅 Calendar ID: {calendar_id}")
    
    if not calendar_id:
        print("   ✗ ERRORE: GOOGLE_CALENDAR_DEFAULT_ID non configurato")
        print("   Aggiungi questa configurazione in settings_local.py")
        print("   O imposta la variabile d'ambiente GOOGLE_CALENDAR_ID")
        return False
    
    print("   ✓ Calendar ID configurato")
    print()
    
    # 5. Verifica occorrenze da sincronizzare
    print("📊 Statistiche occorrenze:")
    total = ScadenzaOccorrenza.objects.count()
    synced = ScadenzaOccorrenza.objects.exclude(google_calendar_event_id='').count()
    not_synced = ScadenzaOccorrenza.objects.filter(google_calendar_event_id='').count()
    annullate = ScadenzaOccorrenza.objects.filter(
        stato=ScadenzaOccorrenza.Stato.ANNULLATA
    ).count()
    
    print(f"   Totale occorrenze: {total}")
    print(f"   Sincronizzate: {synced}")
    print(f"   Non sincronizzate: {not_synced}")
    print(f"   Annullate: {annullate}")
    print()
    
    # 6. Test di connessione (opzionale)
    print("🔗 Test di connessione:")
    try:
        from scadenze.services import GoogleCalendarSync
        sync = GoogleCalendarSync()
        print("   ✓ GoogleCalendarSync inizializzato correttamente")
        print()
        print("=" * 60)
        print("✅ CONFIGURAZIONE OK!")
        print("=" * 60)
        print()
        print("Prossimi passi:")
        print("1. Assicurati di aver condiviso il calendario con:")
        print(f"   {creds_data.get('client_email')}")
        print()
        print("2. Testa la sincronizzazione con:")
        print("   python manage.py sync_google_calendar --dry-run")
        print()
        print("3. Se il test funziona, sincronizza le occorrenze:")
        print("   python manage.py sync_google_calendar --all")
        return True
        
    except Exception as e:
        print(f"   ✗ ERRORE nell'inizializzazione: {e}")
        print()
        print("   Possibili cause:")
        print("   - File credenziali corrotto")
        print("   - Librerie Google non installate")
        print("   - Permessi insufficienti")
        return False


if __name__ == '__main__':
    try:
        success = check_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerifica interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ ERRORE INATTESO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
