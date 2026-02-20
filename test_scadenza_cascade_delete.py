#!/usr/bin/env python
"""
Script di test per verificare la fix del bug IntegrityError su cancellazione Scadenza.
Crea una scadenza con occorrenze, log, alert e webhook, poi la elimina.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from scadenze.models import (
    Scadenza,
    ScadenzaOccorrenza,
    ScadenzaNotificaLog,
    ScadenzaAlert,
    ScadenzaWebhookPayload,
)


def test_cascade_delete():
    """Test della fix per l'IntegrityError su cancellazione Scadenza."""
    
    print("=" * 70)
    print("TEST: Cancellazione Scadenza con CASCADE completo")
    print("=" * 70)
    
    with transaction.atomic():
        # 1. Crea scadenza
        print("\n1️⃣  Creazione Scadenza...")
        scadenza = Scadenza.objects.create(
            titolo="TEST - Scadenza da eliminare",
            descrizione="Test fix IntegrityError CASCADE",
            stato=Scadenza.Stato.ATTIVA,
            priorita=Scadenza.Priorita.MEDIA,
        )
        print(f"   ✓ Scadenza creata: ID={scadenza.id}, Titolo='{scadenza.titolo}'")
        
        # 2. Crea occorrenze
        print("\n2️⃣  Creazione Occorrenze...")
        occorrenze = []
        for i in range(3):
            occ = ScadenzaOccorrenza.objects.create(
                scadenza=scadenza,
                titolo=f"Occorrenza Test {i+1}",
                inizio=timezone.now() + timedelta(days=i),
                stato=ScadenzaOccorrenza.Stato.PENDENTE,
            )
            occorrenze.append(occ)
            print(f"   ✓ Occorrenza {i+1} creata: ID={occ.id}")
        
        # 3. Crea log, alert e webhook per ogni occorrenza
        print("\n3️⃣  Creazione Log, Alert e Webhook...")
        total_logs = 0
        total_alerts = 0
        total_webhooks = 0
        
        for i, occ in enumerate(occorrenze):
            # Log
            for j in range(2):
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occ,
                    evento=ScadenzaNotificaLog.Evento.ALERT_PROGRAMMATO,
                    esito=True,
                    messaggio=f"Test log {j+1} per occorrenza {i+1}",
                )
                total_logs += 1
            
            # Alert
            for j in range(2):
                ScadenzaAlert.objects.create(
                    occorrenza=occ,
                    offset_alert_periodo=ScadenzaAlert.TipoPeriodo.GIORNI,
                    offset_alert=1,
                    metodo_alert=ScadenzaAlert.MetodoAlert.EMAIL,
                    stato=ScadenzaAlert.Stato.PENDENTE,
                )
                total_alerts += 1
            
            # Webhook
            ScadenzaWebhookPayload.objects.create(
                occorrenza=occ,
                destinazione="https://example.com/webhook/test",
                payload={"test": f"occorrenza_{i+1}"},
            )
            total_webhooks += 1
        
        print(f"   ✓ {total_logs} ScadenzaNotificaLog creati")
        print(f"   ✓ {total_alerts} ScadenzaAlert creati")
        print(f"   ✓ {total_webhooks} ScadenzaWebhookPayload creati")
        
        # 4. Verifica conteggi prima dell'eliminazione
        print("\n4️⃣  Verifica conteggi PRIMA eliminazione...")
        print(f"   • Scadenze: {Scadenza.objects.count()}")
        print(f"   • Occorrenze: {ScadenzaOccorrenza.objects.count()}")
        print(f"   • NotificaLog: {ScadenzaNotificaLog.objects.count()}")
        print(f"   • Alert: {ScadenzaAlert.objects.count()}")
        print(f"   • WebhookPayload: {ScadenzaWebhookPayload.objects.count()}")
        
        scadenza_id = scadenza.id
        occorrenza_ids = [occ.id for occ in occorrenze]
        
        # 5. ELIMINA LA SCADENZA (questo è il test principale!)
        print("\n5️⃣  ELIMINAZIONE Scadenza...")
        print(f"   → Eliminando scadenza ID={scadenza_id}...")
        
        try:
            scadenza.delete()
            print("   ✅ SUCCESSO! Scadenza eliminata senza errori")
        except Exception as e:
            print(f"   ❌ ERRORE: {type(e).__name__}: {e}")
            raise
        
        # 6. Verifica che tutto sia stato eliminato
        print("\n6️⃣  Verifica conteggi DOPO eliminazione...")
        
        assert not Scadenza.objects.filter(id=scadenza_id).exists(), \
            "❌ La scadenza non è stata eliminata!"
        print("   ✓ Scadenza eliminata correttamente")
        
        assert not ScadenzaOccorrenza.objects.filter(id__in=occorrenza_ids).exists(), \
            "❌ Le occorrenze non sono state eliminate!"
        print("   ✓ Tutte le occorrenze eliminate (CASCADE)")
        
        # Verifica che TUTTI i log/alert/webhook siano stati eliminati
        remaining_logs = ScadenzaNotificaLog.objects.filter(
            occorrenza_id__in=occorrenza_ids
        ).count()
        assert remaining_logs == 0, \
            f"❌ Ci sono ancora {remaining_logs} log orfani!"
        print("   ✓ Tutti i ScadenzaNotificaLog eliminati (CASCADE)")
        
        remaining_alerts = ScadenzaAlert.objects.filter(
            occorrenza_id__in=occorrenza_ids
        ).count()
        assert remaining_alerts == 0, \
            f"❌ Ci sono ancora {remaining_alerts} alert orfani!"
        print("   ✓ Tutti gli ScadenzaAlert eliminati (CASCADE)")
        
        remaining_webhooks = ScadenzaWebhookPayload.objects.filter(
            occorrenza_id__in=occorrenza_ids
        ).count()
        assert remaining_webhooks == 0, \
            f"❌ Ci sono ancora {remaining_webhooks} webhook orfani!"
        print("   ✓ Tutti gli ScadenzaWebhookPayload eliminati (CASCADE)")
        
        print("\n" + "=" * 70)
        print("✅ TEST SUPERATO! La fix funziona correttamente!")
        print("=" * 70)
        
        # ROLLBACK della transazione (non vogliamo lasciare dati di test)
        raise Exception("ROLLBACK - Test completato con successo")


if __name__ == "__main__":
    try:
        test_cascade_delete()
    except Exception as e:
        if "ROLLBACK" in str(e):
            print("\n🔄 Rollback eseguito - database pulito")
            sys.exit(0)
        else:
            print(f"\n❌ Test fallito: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
