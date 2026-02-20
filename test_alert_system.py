#!/usr/bin/env python
"""
Script di test completo per il sistema di alert delle scadenze.
Verifica configurazione, validazione e funzionamento end-to-end.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.utils import timezone
from django.core.exceptions import ValidationError
from scadenze.models import Scadenza, ScadenzaOccorrenza, ScadenzaAlert, ScadenzaNotificaLog
from scadenze.services import AlertDispatcher


class TestAlertSystem:
    """Test suite per il sistema di alert"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name, func):
        """Esegue un singolo test"""
        try:
            print(f"\n{'='*60}")
            print(f"TEST: {name}")
            print('='*60)
            func()
            print(f"✅ PASSED")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.errors.append((name, str(e)))
        except Exception as e:
            print(f"💥 ERROR: {e}")
            self.failed += 1
            self.errors.append((name, f"Exception: {e}"))
    
    def report(self):
        """Stampa report finale"""
        print(f"\n\n{'='*60}")
        print("REPORT FINALE")
        print('='*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total:  {self.passed + self.failed}")
        
        if self.errors:
            print(f"\n{'='*60}")
            print("ERRORI DETTAGLIATI")
            print('='*60)
            for name, error in self.errors:
                print(f"\n❌ {name}")
                print(f"   {error}")
        
        return self.failed == 0


def test_1_database_structure():
    """Verifica struttura database"""
    print("Controllo esistenza tabelle...")
    
    # Conta record
    scadenze = Scadenza.objects.count()
    occorrenze = ScadenzaOccorrenza.objects.count()
    alert = ScadenzaAlert.objects.count()
    logs = ScadenzaNotificaLog.objects.count()
    
    print(f"  - Scadenze: {scadenze}")
    print(f"  - Occorrenze: {occorrenze}")
    print(f"  - Alert: {alert}")
    print(f"  - Log: {logs}")
    
    assert alert > 0, "Nessun alert trovato nel database"


def test_2_alert_configuration_email():
    """Verifica configurazione alert email"""
    print("Verifico alert email...")
    
    # Alert email con destinatari
    email_ok = ScadenzaAlert.objects.filter(
        metodo_alert='email',
        alert_config__destinatari__isnull=False
    ).exclude(alert_config={}).count()
    
    # Alert email con destinatari nella scadenza
    email_scadenza = ScadenzaAlert.objects.filter(
        metodo_alert='email',
        occorrenza__scadenza__comunicazione_destinatari__gt=''
    ).count()
    
    # Alert email SENZA destinatari
    email_no_dest = ScadenzaAlert.objects.filter(
        metodo_alert='email',
        alert_config={},
        occorrenza__scadenza__comunicazione_destinatari=''
    ).count()
    
    print(f"  - Alert email con destinatari in config: {email_ok}")
    print(f"  - Alert email con destinatari in scadenza: {email_scadenza}")
    print(f"  - Alert email SENZA destinatari: {email_no_dest}")
    
    if email_no_dest > 0:
        print(f"\n⚠️  ATTENZIONE: {email_no_dest} alert email non hanno destinatari configurati!")
        print("     Questi alert falliranno durante l'invio.")


def test_3_alert_configuration_webhook():
    """Verifica configurazione alert webhook"""
    print("Verifico alert webhook...")
    
    # Alert webhook con URL
    webhook_ok = ScadenzaAlert.objects.filter(
        metodo_alert='webhook',
        alert_config__url__isnull=False
    ).exclude(alert_config={}).count()
    
    # Alert webhook SENZA URL
    webhook_no_url = ScadenzaAlert.objects.filter(
        metodo_alert='webhook',
        alert_config={}
    ).count()
    
    print(f"  - Alert webhook con URL configurato: {webhook_ok}")
    print(f"  - Alert webhook SENZA URL: {webhook_no_url}")
    
    if webhook_no_url > 0:
        print(f"\n⚠️  ATTENZIONE: {webhook_no_url} alert webhook non hanno URL configurato!")
        print("     Questi alert falliranno durante l'invio.")


def test_4_alert_timing():
    """Verifica timing degli alert"""
    print("Verifico timing alert...")
    
    now = timezone.now()
    
    # Alert programmati
    programmati = ScadenzaAlert.objects.filter(
        alert_programmata_il__isnull=False
    ).count()
    
    # Alert scaduti ma non inviati
    scaduti = ScadenzaAlert.objects.filter(
        stato='pending',
        alert_programmata_il__lt=now
    ).count()
    
    # Alert futuri
    futuri = ScadenzaAlert.objects.filter(
        stato='pending',
        alert_programmata_il__gte=now
    ).count()
    
    print(f"  - Alert con timing programmato: {programmati}")
    print(f"  - Alert SCADUTI non inviati: {scaduti}")
    print(f"  - Alert futuri: {futuri}")
    
    if scaduti > 0:
        print(f"\n⚠️  PROBLEMA: {scaduti} alert sono scaduti ma non sono stati inviati!")
        print("     Probabilmente il cron job non è configurato.")


def test_5_validation_email_no_dest():
    """Test validazione: email senza destinatari"""
    print("Test validazione email senza destinatari...")
    
    # Crea scadenza senza destinatari
    scadenza = Scadenza.objects.create(
        titolo="Test Validazione Email",
        comunicazione_destinatari=""  # Vuoto!
    )
    
    occorrenza = ScadenzaOccorrenza.objects.create(
        scadenza=scadenza,
        inizio=timezone.now() + timedelta(days=7)
    )
    
    # Prova a creare alert senza destinatari
    alert = ScadenzaAlert(
        occorrenza=occorrenza,
        metodo_alert='email',
        offset_alert=1,
        offset_alert_periodo='days',
        alert_config={}  # Vuoto!
    )
    
    try:
        alert.full_clean()  # Dovrebbe fallire
        print("  ❌ La validazione NON ha bloccato l'alert senza destinatari!")
        raise AssertionError("Validazione email fallita - alert senza destinatari accettato")
    except ValidationError as e:
        print(f"  ✅ Validazione corretta: {e}")
    finally:
        # Cleanup
        occorrenza.delete()
        scadenza.delete()


def test_6_validation_webhook_no_url():
    """Test validazione: webhook senza URL"""
    print("Test validazione webhook senza URL...")
    
    scadenza = Scadenza.objects.create(
        titolo="Test Validazione Webhook"
    )
    
    occorrenza = ScadenzaOccorrenza.objects.create(
        scadenza=scadenza,
        inizio=timezone.now() + timedelta(days=7)
    )
    
    # Prova a creare alert webhook senza URL
    alert = ScadenzaAlert(
        occorrenza=occorrenza,
        metodo_alert='webhook',
        offset_alert=1,
        offset_alert_periodo='hours',
        alert_config={}  # Vuoto!
    )
    
    try:
        alert.full_clean()  # Dovrebbe fallire
        print("  ❌ La validazione NON ha bloccato il webhook senza URL!")
        raise AssertionError("Validazione webhook fallita - alert senza URL accettato")
    except ValidationError as e:
        print(f"  ✅ Validazione corretta: {e}")
    finally:
        # Cleanup
        occorrenza.delete()
        scadenza.delete()


def test_7_alert_timing_calculation():
    """Test calcolo automatico timing alert"""
    print("Test calcolo timing alert...")
    
    scadenza = Scadenza.objects.create(
        titolo="Test Timing",
        comunicazione_destinatari="test@example.com"
    )
    
    # Occorrenza tra 10 giorni
    inizio = timezone.now() + timedelta(days=10)
    occorrenza = ScadenzaOccorrenza.objects.create(
        scadenza=scadenza,
        inizio=inizio
    )
    
    # Alert 3 giorni prima
    alert = ScadenzaAlert.objects.create(
        occorrenza=occorrenza,
        metodo_alert='email',
        offset_alert=3,
        offset_alert_periodo='days',
        alert_config={'destinatari': 'test@example.com'}
    )
    
    # Verifica calcolo
    expected = inizio - timedelta(days=3)
    actual = alert.alert_programmata_il
    
    print(f"  - Occorrenza inizio: {inizio}")
    print(f"  - Alert timing atteso: {expected}")
    print(f"  - Alert timing calcolato: {actual}")
    
    # Tolleranza di 1 secondo per differenze di arrotondamento
    diff = abs((expected - actual).total_seconds())
    assert diff < 1, f"Timing calcolato errato: differenza di {diff} secondi"
    
    print("  ✅ Timing calcolato correttamente")
    
    # Cleanup
    alert.delete()
    occorrenza.delete()
    scadenza.delete()


def test_8_alert_dispatcher_structure():
    """Test struttura AlertDispatcher"""
    print("Test struttura AlertDispatcher...")
    
    dispatcher = AlertDispatcher()
    
    # Verifica metodi esistenti
    assert hasattr(dispatcher, 'dispatch_alert'), "Metodo dispatch_alert mancante"
    assert hasattr(dispatcher, 'dispatch_occorrenza_alerts'), "Metodo dispatch_occorrenza_alerts mancante"
    assert hasattr(dispatcher, '_send_email_alert'), "Metodo _send_email_alert mancante"
    assert hasattr(dispatcher, '_send_webhook_alert'), "Metodo _send_webhook_alert mancante"
    
    print("  ✅ Tutti i metodi del dispatcher sono presenti")


def test_9_cron_job_configuration():
    """Test configurazione cron job"""
    print("Test configurazione cron job...")
    
    import subprocess
    
    try:
        result = subprocess.run(['crontab', '-l'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        crontab = result.stdout
        
        has_alert_cron = 'send_scheduled_alerts' in crontab
        
        print(f"  - Crontab configurato: {bool(crontab)}")
        print(f"  - Comando send_scheduled_alerts presente: {has_alert_cron}")
        
        if not has_alert_cron:
            print("\n  ⚠️  PROBLEMA CRITICO: Cron job per send_scheduled_alerts NON configurato!")
            print("     Gli alert NON verranno inviati automaticamente.")
            print("\n  📝 Aggiungi al crontab:")
            print("     */10 * * * * cd /home/sandro/mygest && source venv/bin/activate && python manage.py send_scheduled_alerts >> /home/sandro/mygest/logs/alerts.log 2>&1")
            
            raise AssertionError("Cron job send_scheduled_alerts non configurato")
        
    except subprocess.TimeoutExpired:
        print("  ⚠️  Timeout durante il controllo del crontab")
    except FileNotFoundError:
        print("  ⚠️  Comando crontab non trovato")


def test_10_problematic_alerts():
    """Analisi alert problematici esistenti"""
    print("Analisi alert con problemi di configurazione...")
    
    now = timezone.now()
    
    # Alert scaduti non inviati
    scaduti = ScadenzaAlert.objects.filter(
        stato='pending',
        alert_programmata_il__lt=now
    ).select_related('occorrenza__scadenza')
    
    if scaduti.exists():
        print(f"\n  ⚠️  Trovati {scaduti.count()} alert scaduti non inviati:")
        for alert in scaduti[:5]:
            print(f"     - ID {alert.pk}: {alert.occorrenza.scadenza.titolo}")
            print(f"       Doveva essere inviato: {alert.alert_programmata_il}")
            print(f"       Metodo: {alert.metodo_alert}")
            
            # Verifica configurazione
            if alert.metodo_alert == 'email':
                dest_config = alert.alert_config.get('destinatari', '')
                dest_scad = alert.occorrenza.scadenza.comunicazione_destinatari
                if not dest_config and not dest_scad:
                    print(f"       ❌ PROBLEMA: Nessun destinatario configurato!")
            elif alert.metodo_alert == 'webhook':
                url = alert.alert_config.get('url', '')
                if not url:
                    print(f"       ❌ PROBLEMA: Nessun URL configurato!")
    else:
        print("  ✅ Nessun alert scaduto non inviato")


def main():
    """Esegue tutti i test"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        TEST SUITE - Sistema Alert Scadenze MyGest           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    suite = TestAlertSystem()
    
    # Esegui test
    suite.test("1. Struttura Database", test_1_database_structure)
    suite.test("2. Configurazione Alert Email", test_2_alert_configuration_email)
    suite.test("3. Configurazione Alert Webhook", test_3_alert_configuration_webhook)
    suite.test("4. Timing Alert", test_4_alert_timing)
    suite.test("5. Validazione Email senza Destinatari", test_5_validation_email_no_dest)
    suite.test("6. Validazione Webhook senza URL", test_6_validation_webhook_no_url)
    suite.test("7. Calcolo Automatico Timing", test_7_alert_timing_calculation)
    suite.test("8. Struttura AlertDispatcher", test_8_alert_dispatcher_structure)
    suite.test("9. Configurazione Cron Job", test_9_cron_job_configuration)
    suite.test("10. Alert Problematici Esistenti", test_10_problematic_alerts)
    
    # Report finale
    success = suite.report()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
