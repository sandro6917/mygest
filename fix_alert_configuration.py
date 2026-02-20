#!/usr/bin/env python
"""
Script per correggere automaticamente la configurazione degli alert problematici.

Uso:
    python fix_alert_configuration.py --dry-run    # Mostra cosa verrebbe fatto
    python fix_alert_configuration.py              # Applica le correzioni
    python fix_alert_configuration.py --help       # Mostra help
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from scadenze.models import ScadenzaAlert, Scadenza


def print_header(text):
    """Stampa intestazione formattata"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)


def analyze_problematic_alerts():
    """Analizza e identifica alert con problemi di configurazione"""
    
    problems = {
        'email_no_dest': [],
        'webhook_no_url': [],
        'overdue': []
    }
    
    now = timezone.now()
    
    # 1. Alert email senza destinatari
    email_alerts = ScadenzaAlert.objects.filter(
        metodo_alert='email',
        alert_config={},
        occorrenza__scadenza__comunicazione_destinatari=''
    ).select_related('occorrenza__scadenza')
    
    for alert in email_alerts:
        problems['email_no_dest'].append({
            'alert': alert,
            'scadenza': alert.occorrenza.scadenza,
            'occorrenza': alert.occorrenza
        })
    
    # 2. Alert webhook senza URL
    webhook_alerts = ScadenzaAlert.objects.filter(
        metodo_alert='webhook',
        alert_config={}
    ).select_related('occorrenza__scadenza')
    
    for alert in webhook_alerts:
        problems['webhook_no_url'].append({
            'alert': alert,
            'scadenza': alert.occorrenza.scadenza,
            'occorrenza': alert.occorrenza
        })
    
    # 3. Alert scaduti non inviati
    overdue_alerts = ScadenzaAlert.objects.filter(
        stato='pending',
        alert_programmata_il__lt=now
    ).select_related('occorrenza__scadenza').order_by('alert_programmata_il')
    
    for alert in overdue_alerts:
        problems['overdue'].append({
            'alert': alert,
            'scadenza': alert.occorrenza.scadenza,
            'occorrenza': alert.occorrenza
        })
    
    return problems


def print_problems_summary(problems):
    """Stampa riepilogo problemi trovati"""
    
    print_header("ANALISI PROBLEMI ALERT")
    
    total_issues = (
        len(problems['email_no_dest']) +
        len(problems['webhook_no_url']) +
        len(problems['overdue'])
    )
    
    if total_issues == 0:
        print("✅ Nessun problema trovato! Sistema configurato correttamente.")
        return False
    
    print(f"\n📊 Totale problemi trovati: {total_issues}\n")
    
    # Email senza destinatari
    if problems['email_no_dest']:
        print(f"⚠️  {len(problems['email_no_dest'])} alert EMAIL senza destinatari:")
        for item in problems['email_no_dest']:
            alert = item['alert']
            print(f"    - ID {alert.pk}: {alert.occorrenza.scadenza.titolo}")
            print(f"      Programmato: {alert.alert_programmata_il}")
    
    # Webhook senza URL
    if problems['webhook_no_url']:
        print(f"\n⚠️  {len(problems['webhook_no_url'])} alert WEBHOOK senza URL:")
        for item in problems['webhook_no_url']:
            alert = item['alert']
            print(f"    - ID {alert.pk}: {alert.occorrenza.scadenza.titolo}")
            print(f"      Programmato: {alert.alert_programmata_il}")
    
    # Alert scaduti
    if problems['overdue']:
        print(f"\n⏰ {len(problems['overdue'])} alert SCADUTI non inviati:")
        for item in problems['overdue']:
            alert = item['alert']
            scaduto_da = timezone.now() - alert.alert_programmata_il
            giorni = scaduto_da.days
            ore = scaduto_da.seconds // 3600
            
            print(f"    - ID {alert.pk}: {alert.occorrenza.scadenza.titolo}")
            print(f"      Doveva essere inviato: {alert.alert_programmata_il}")
            print(f"      Scaduto da: {giorni} giorni e {ore} ore")
            print(f"      Tipo: {alert.get_metodo_alert_display()}")
    
    return True


def fix_email_alerts(problems, dry_run=False, default_email=None):
    """Corregge alert email senza destinatari"""
    
    if not problems['email_no_dest']:
        return 0
    
    print_header("FIX ALERT EMAIL")
    
    if not default_email and not dry_run:
        print("\n❓ Inserisci email di default per alert senza destinatari:")
        print("   (lascia vuoto per configurare scadenza per scadenza)")
        default_email = input("   Email: ").strip()
    
    fixed = 0
    
    for item in problems['email_no_dest']:
        alert = item['alert']
        scadenza = item['scadenza']
        
        print(f"\n📧 Alert ID {alert.pk}: {scadenza.titolo}")
        
        if dry_run:
            print("   [DRY RUN] Verrebbe configurato con destinatari")
            fixed += 1
            continue
        
        # Chiedi destinatari specifici o usa default
        if default_email:
            destinatari = default_email
        else:
            print(f"   Inserisci destinatari per questa scadenza:")
            destinatari = input("   Email (separa con virgola): ").strip()
        
        if not destinatari:
            print("   ⏭️  Saltato (nessun destinatario fornito)")
            continue
        
        # Applica fix alla scadenza (così tutti gli alert ne beneficiano)
        scadenza.comunicazione_destinatari = destinatari
        scadenza.save()
        
        print(f"   ✅ Configurato: {destinatari}")
        fixed += 1
    
    return fixed


def fix_webhook_alerts(problems, dry_run=False, default_url=None):
    """Corregge alert webhook senza URL"""
    
    if not problems['webhook_no_url']:
        return 0
    
    print_header("FIX ALERT WEBHOOK")
    
    if not default_url and not dry_run:
        print("\n❓ Inserisci URL webhook di default:")
        print("   (lascia vuoto per configurare alert per alert)")
        default_url = input("   URL: ").strip()
    
    fixed = 0
    
    for item in problems['webhook_no_url']:
        alert = item['alert']
        scadenza = item['scadenza']
        
        print(f"\n🔗 Alert ID {alert.pk}: {scadenza.titolo}")
        
        if dry_run:
            print("   [DRY RUN] Verrebbe configurato con URL webhook")
            fixed += 1
            continue
        
        # Chiedi URL specifico o usa default
        if default_url:
            url = default_url
        else:
            print(f"   Inserisci URL webhook per questo alert:")
            url = input("   URL: ").strip()
        
        if not url:
            print("   ⏭️  Saltato (nessun URL fornito)")
            continue
        
        # Applica fix all'alert
        alert.alert_config = {'url': url, 'timeout': 10}
        alert.save()
        
        print(f"   ✅ Configurato: {url}")
        fixed += 1
    
    return fixed


def handle_overdue_alerts(problems, dry_run=False):
    """Gestisce alert scaduti"""
    
    if not problems['overdue']:
        return 0
    
    print_header("GESTIONE ALERT SCADUTI")
    
    print("\nTrovati alert scaduti. Opzioni disponibili:")
    print("  1. Inviarli ora (se ancora rilevanti)")
    print("  2. Segnarli come annullati")
    print("  3. Lasciare pendenti (li invierà il cron job)")
    print("  4. Revisione manuale uno per uno")
    
    if dry_run:
        print("\n[DRY RUN] In modalità normale, chiederemmo cosa fare")
        return 0
    
    scelta = input("\nScegli opzione (1-4): ").strip()
    
    handled = 0
    
    if scelta == '1':
        # Invia ora
        from scadenze.services import AlertDispatcher
        dispatcher = AlertDispatcher()
        
        print("\n🚀 Invio alert scaduti...")
        for item in problems['overdue']:
            alert = item['alert']
            try:
                dispatcher.dispatch_alert(alert)
                print(f"   ✅ ID {alert.pk} inviato")
                handled += 1
            except Exception as e:
                print(f"   ❌ ID {alert.pk} fallito: {e}")
    
    elif scelta == '2':
        # Annulla
        print("\n🚫 Annullamento alert scaduti...")
        for item in problems['overdue']:
            alert = item['alert']
            alert.stato = 'cancelled'
            alert.save()
            print(f"   ✅ ID {alert.pk} annullato")
            handled += 1
    
    elif scelta == '3':
        # Lascia pendenti
        print("\n⏸️  Alert lasciati pendenti, verranno processati dal cron job")
        handled = 0
    
    elif scelta == '4':
        # Revisione manuale
        print("\n🔍 Revisione manuale alert:")
        for item in problems['overdue']:
            alert = item['alert']
            print(f"\n  Alert ID {alert.pk}")
            print(f"  Scadenza: {alert.occorrenza.scadenza.titolo}")
            print(f"  Doveva essere inviato: {alert.alert_programmata_il}")
            print(f"  Tipo: {alert.get_metodo_alert_display()}")
            
            azione = input("  Azione (i=invia, a=annulla, s=salta): ").strip().lower()
            
            if azione == 'i':
                try:
                    from scadenze.services import AlertDispatcher
                    dispatcher = AlertDispatcher()
                    dispatcher.dispatch_alert(alert)
                    print(f"   ✅ Inviato")
                    handled += 1
                except Exception as e:
                    print(f"   ❌ Errore: {e}")
            elif azione == 'a':
                alert.stato = 'cancelled'
                alert.save()
                print(f"   ✅ Annullato")
                handled += 1
            else:
                print(f"   ⏭️  Saltato")
    
    return handled


def main():
    """Funzione principale"""
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    auto_mode = '--auto' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        return 0
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║       FIX CONFIGURAZIONE ALERT - Sistema Scadenze MyGest        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if dry_run:
        print("🔍 Modalità DRY RUN - Nessuna modifica verrà applicata\n")
    
    # Analizza problemi
    problems = analyze_problematic_alerts()
    
    # Mostra riepilogo
    has_problems = print_problems_summary(problems)
    
    if not has_problems:
        return 0
    
    if dry_run:
        print("\n💡 Per applicare le correzioni, esegui senza --dry-run")
        return 0
    
    # Conferma
    print("\n" + "="*70)
    risposta = input("Vuoi procedere con le correzioni? (s/n): ").strip().lower()
    
    if risposta not in ['s', 'si', 'y', 'yes']:
        print("\n❌ Operazione annullata.")
        return 1
    
    # Applica fix
    with transaction.atomic():
        fixed_email = fix_email_alerts(problems, dry_run=False)
        fixed_webhook = fix_webhook_alerts(problems, dry_run=False)
        handled_overdue = handle_overdue_alerts(problems, dry_run=False)
    
    # Report finale
    print_header("RIEPILOGO CORREZIONI")
    print(f"\n✅ Alert email corretti: {fixed_email}")
    print(f"✅ Alert webhook corretti: {fixed_webhook}")
    print(f"✅ Alert scaduti gestiti: {handled_overdue}")
    print(f"\n📊 Totale operazioni: {fixed_email + fixed_webhook + handled_overdue}")
    
    print("\n" + "="*70)
    print("✅ Operazione completata!")
    print("\n💡 Prossimi passi:")
    print("   1. Verifica la configurazione del cron job")
    print("   2. Testa l'invio manuale: python manage.py send_scheduled_alerts --dry-run")
    print("   3. Monitora i log: tail -f logs/alerts.log")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
