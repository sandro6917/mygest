"""Test per verificare la corretta eliminazione CASCADE di Scadenza e modelli correlati."""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import connection
from model_bakery import baker

from scadenze.models import (
    Scadenza,
    ScadenzaOccorrenza,
    ScadenzaNotificaLog,
    ScadenzaAlert,
    ScadenzaWebhookPayload,
)


# Skip se non PostgreSQL (SQLite ha problemi con DEFERRABLE constraints)
pytestmark = pytest.mark.skipif(
    connection.vendor != 'postgresql',
    reason="Questi test richiedono PostgreSQL con constraint DEFERRABLE"
)


@pytest.mark.django_db(transaction=True)
class TestScadenzaCascadeDelete:
    """Test per la fix del bug IntegrityError su cancellazione Scadenza."""

    def test_delete_scadenza_with_occorrenze_and_logs(self):
        """
        Test che verifica l'eliminazione CASCADE completa di:
        - Scadenza
          └─> ScadenzaOccorrenza
               ├─> ScadenzaNotificaLog
               ├─> ScadenzaAlert
               └─> ScadenzaWebhookPayload
        
        Questo test verifica la fix per l'IntegrityError che si verificava
        quando i constraint FK non erano DEFERRABLE.
        """
        # Setup: Crea una scadenza con occorrenze e relativi log/alert/webhook
        scadenza = baker.make(
            Scadenza,
            titolo="Test Scadenza",
            stato=Scadenza.Stato.ATTIVA,
        )
        
        # Crea 3 occorrenze
        occorrenze = []
        for i in range(3):
            occ = baker.make(
                ScadenzaOccorrenza,
                scadenza=scadenza,
                titolo=f"Occorrenza {i+1}",
                inizio=timezone.now() + timedelta(days=i),
                stato=ScadenzaOccorrenza.Stato.PENDENTE,
            )
            occorrenze.append(occ)
        
        # Per ogni occorrenza, crea log, alert e webhook
        for occ in occorrenze:
            # Crea 2 log eventi
            baker.make(
                ScadenzaNotificaLog,
                occorrenza=occ,
                evento=ScadenzaNotificaLog.Evento.ALERT_PROGRAMMATO,
                esito=True,
                messaggio="Alert programmato",
                _quantity=2,
            )
            
            # Crea 2 alert
            baker.make(
                ScadenzaAlert,
                occorrenza=occ,
                offset_alert_periodo=ScadenzaAlert.TipoPeriodo.GIORNI,
                offset_alert=1,
                metodo_alert=ScadenzaAlert.MetodoAlert.EMAIL,
                stato=ScadenzaAlert.Stato.PENDENTE,
                _quantity=2,
            )
            
            # Crea 1 webhook payload
            baker.make(
                ScadenzaWebhookPayload,
                occorrenza=occ,
                destinazione="https://example.com/webhook",
                payload={"test": "data"},
            )
        
        # Verifica che i dati siano stati creati correttamente
        assert Scadenza.objects.count() == 1
        assert ScadenzaOccorrenza.objects.count() == 3
        assert ScadenzaNotificaLog.objects.count() == 6  # 3 occorrenze * 2 log
        assert ScadenzaAlert.objects.count() == 6  # 3 occorrenze * 2 alert
        assert ScadenzaWebhookPayload.objects.count() == 3  # 3 occorrenze * 1 webhook
        
        # Salva l'ID della scadenza per verificare dopo
        scadenza_id = scadenza.id
        occorrenza_ids = [occ.id for occ in occorrenze]
        
        # ACT: Elimina la scadenza
        # Questo dovrebbe eliminare tutto in cascata senza errori
        scadenza.delete()
        
        # ASSERT: Verifica che tutto sia stato eliminato
        assert not Scadenza.objects.filter(id=scadenza_id).exists()
        assert not ScadenzaOccorrenza.objects.filter(id__in=occorrenza_ids).exists()
        assert ScadenzaNotificaLog.objects.count() == 0
        assert ScadenzaAlert.objects.count() == 0
        assert ScadenzaWebhookPayload.objects.count() == 0

    def test_delete_scadenza_occorrenza_with_related_objects(self):
        """
        Test che verifica l'eliminazione CASCADE di una singola occorrenza
        con i suoi log/alert/webhook.
        """
        scadenza = baker.make(Scadenza, periodicita=Scadenza.Periodicita.MENSILE)
        
        # Crea 2 occorrenze
        occ1 = baker.make(ScadenzaOccorrenza, scadenza=scadenza)
        occ2 = baker.make(ScadenzaOccorrenza, scadenza=scadenza)
        
        # Aggiungi log/alert/webhook solo a occ1
        baker.make(ScadenzaNotificaLog, occorrenza=occ1, _quantity=2)
        baker.make(ScadenzaAlert, occorrenza=occ1, _quantity=2)
        baker.make(ScadenzaWebhookPayload, occorrenza=occ1)
        
        # Verifica conteggi iniziali
        assert ScadenzaOccorrenza.objects.count() == 2
        assert ScadenzaNotificaLog.objects.count() == 2
        assert ScadenzaAlert.objects.count() == 2
        assert ScadenzaWebhookPayload.objects.count() == 1
        
        # Elimina solo occ1
        occ1.delete()
        
        # Verifica che occ1 e i suoi oggetti correlati siano stati eliminati
        assert ScadenzaOccorrenza.objects.count() == 1
        assert ScadenzaOccorrenza.objects.filter(id=occ2.id).exists()
        assert ScadenzaNotificaLog.objects.count() == 0
        assert ScadenzaAlert.objects.count() == 0
        assert ScadenzaWebhookPayload.objects.count() == 0
        
        # La scadenza principale deve ancora esistere
        assert Scadenza.objects.filter(id=scadenza.id).exists()

    def test_delete_scadenza_without_occorrenze(self):
        """Test che una scadenza senza occorrenze può essere eliminata."""
        scadenza = baker.make(Scadenza)
        scadenza_id = scadenza.id
        
        # Elimina
        scadenza.delete()
        
        # Verifica
        assert not Scadenza.objects.filter(id=scadenza_id).exists()

    def test_bulk_delete_scadenze_with_complex_relationships(self):
        """
        Test che verifica l'eliminazione massiva di più scadenze
        con relazioni complesse.
        """
        # Crea 5 scadenze, ognuna con occorrenze e oggetti correlati
        scadenze = []
        for i in range(5):
            scadenza = baker.make(Scadenza, titolo=f"Scadenza {i+1}")
            
            # 2 occorrenze per scadenza
            for j in range(2):
                occ = baker.make(ScadenzaOccorrenza, scadenza=scadenza)
                baker.make(ScadenzaNotificaLog, occorrenza=occ)
                baker.make(ScadenzaAlert, occorrenza=occ)
                baker.make(ScadenzaWebhookPayload, occorrenza=occ)
            
            scadenze.append(scadenza)
        
        # Verifica conteggi iniziali
        assert Scadenza.objects.count() == 5
        assert ScadenzaOccorrenza.objects.count() == 10  # 5 * 2
        assert ScadenzaNotificaLog.objects.count() == 10
        assert ScadenzaAlert.objects.count() == 10
        assert ScadenzaWebhookPayload.objects.count() == 10
        
        # Bulk delete delle prime 3 scadenze
        scadenze_ids = [s.id for s in scadenze[:3]]
        Scadenza.objects.filter(id__in=scadenze_ids).delete()
        
        # Verifica conteggi dopo eliminazione
        assert Scadenza.objects.count() == 2
        assert ScadenzaOccorrenza.objects.count() == 4  # 2 * 2
        assert ScadenzaNotificaLog.objects.count() == 4
        assert ScadenzaAlert.objects.count() == 4
        assert ScadenzaWebhookPayload.objects.count() == 4

    def test_delete_preserves_unrelated_data(self):
        """
        Test che verifica che l'eliminazione di una scadenza
        non influenzi scadenze non correlate.
        """
        # Crea 2 scadenze separate
        scadenza1 = baker.make(Scadenza, titolo="Scadenza 1")
        scadenza2 = baker.make(Scadenza, titolo="Scadenza 2")
        
        # Aggiungi occorrenze a entrambe
        occ1 = baker.make(ScadenzaOccorrenza, scadenza=scadenza1)
        occ2 = baker.make(ScadenzaOccorrenza, scadenza=scadenza2)
        
        baker.make(ScadenzaNotificaLog, occorrenza=occ1)
        baker.make(ScadenzaNotificaLog, occorrenza=occ2)
        
        # Elimina solo scadenza1
        scadenza1.delete()
        
        # Verifica che scadenza2 e i suoi dati esistano ancora
        assert Scadenza.objects.filter(id=scadenza2.id).exists()
        assert ScadenzaOccorrenza.objects.filter(id=occ2.id).exists()
        assert ScadenzaNotificaLog.objects.filter(occorrenza=occ2).exists()
        
        # Verifica che scadenza1 e i suoi dati siano stati eliminati
        assert not Scadenza.objects.filter(id=scadenza1.id).exists()
        assert not ScadenzaOccorrenza.objects.filter(id=occ1.id).exists()
        assert not ScadenzaNotificaLog.objects.filter(occorrenza=occ1).exists()
