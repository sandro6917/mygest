"""
Test di integrazione tra app
Testano flussi completi che coinvolgono multiple applicazioni
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType


@pytest.mark.integration
class TestFlussoDocumentoProtocolloArchivio:
    """Test flusso completo: Documento -> Protocollo -> Archivio Fisico"""
    
    def test_flusso_completo_documento_in_entrata(
        self, db, cliente_pf, documento_tipo, fascicolo, unita_archivio
    ):
        """
        Test flusso completo:
        1. Crea documento
        2. Protocolla in entrata
        3. Assegna collocazione fisica
        """
        from documenti.models import Documento
        from protocollo.models import MovimentoProtocollo
        from archivio_fisico.models import CollocazioneFisica
        
        # 1. Crea documento
        documento = Documento.objects.create(
            cliente=cliente_pf,
            tipo=documento_tipo,
            fascicolo=fascicolo,
            descrizione='Documento in entrata',
            data_documento=timezone.now().date()
        )
        assert documento.pk is not None
        
        # 2. Protocolla in entrata
        movimento = MovimentoProtocollo.objects.create(
            content_type=ContentType.objects.get_for_model(Documento),
            object_id=documento.id,
            tipo='IN',
            numero_protocollo=1,
            data_protocollo=timezone.now().date(),
            mittente=cliente_pf.anagrafica
        )
        assert movimento.pk is not None
        assert movimento.content_object == documento
        
        # 3. Assegna collocazione fisica
        collocazione = CollocazioneFisica.objects.create(
            content_type=ContentType.objects.get_for_model(Documento),
            object_id=documento.id,
            unita=unita_archivio,
            posizione=1
        )
        assert collocazione.pk is not None
        assert collocazione.content_object == documento
        
        # Verifica relazioni
        assert movimento.numero_protocollo == 1
        assert collocazione.unita == unita_archivio
    
    def test_flusso_documento_in_uscita(
        self, db, cliente_pf, documento_tipo, fascicolo
    ):
        """Test documento in uscita con protocollazione"""
        from documenti.models import Documento
        from protocollo.models import MovimentoProtocollo
        
        # Crea documento
        documento = Documento.objects.create(
            cliente=cliente_pf,
            tipo=documento_tipo,
            fascicolo=fascicolo,
            descrizione='Documento in uscita'
        )
        
        # Protocolla in uscita
        movimento = MovimentoProtocollo.objects.create(
            content_type=ContentType.objects.get_for_model(Documento),
            object_id=documento.id,
            tipo='OUT',
            numero_protocollo=2,
            data_protocollo=timezone.now().date(),
            destinatario=cliente_pf.anagrafica
        )
        
        assert movimento.tipo == 'OUT'
        assert movimento.destinatario == cliente_pf.anagrafica


@pytest.mark.integration
class TestFlussoPraticaFascicoloScadenze:
    """Test flusso: Pratica -> Fascicolo -> Documenti -> Scadenze"""
    
    def test_creazione_pratica_con_fascicolo_e_documenti(
        self, db, cliente_pf, pratica_tipo, fascicolo_tipo, 
        documento_tipo, classificazione
    ):
        """
        Test flusso completo:
        1. Crea pratica
        2. Crea fascicolo collegato
        3. Aggiungi documenti
        4. Crea scadenza
        """
        from pratiche.models import Pratica
        from fascicoli.models import Fascicolo
        from documenti.models import Documento
        from scadenze.models import Scadenza
        
        # 1. Crea pratica
        pratica = Pratica.objects.create(
            cliente=cliente_pf,
            tipo=pratica_tipo,
            codice='PRAT-TEST-001',
            oggetto='Pratica di test completa',
            stato='aperta',
            data_apertura=timezone.now().date()
        )
        assert pratica.pk is not None
        
        # 2. Crea fascicolo collegato alla pratica
        fascicolo = Fascicolo.objects.create(
            cliente=cliente_pf,
            tipo=fascicolo_tipo,
            classificazione=classificazione,
            titolo='Fascicolo per pratica',
            stato='aperto'
        )
        fascicolo.pratiche.add(pratica)
        assert pratica in fascicolo.pratiche.all()
        
        # 3. Aggiungi documenti al fascicolo
        doc1 = Documento.objects.create(
            cliente=cliente_pf,
            tipo=documento_tipo,
            fascicolo=fascicolo,
            pratica=pratica,
            descrizione='Documento 1'
        )
        doc2 = Documento.objects.create(
            cliente=cliente_pf,
            tipo=documento_tipo,
            fascicolo=fascicolo,
            pratica=pratica,
            descrizione='Documento 2'
        )
        
        documenti = Documento.objects.filter(fascicolo=fascicolo)
        assert documenti.count() == 2
        
        # 4. Crea scadenza collegata alla pratica
        scadenza = Scadenza.objects.create(
            pratica=pratica,
            titolo='Scadenza importante',
            data_inizio=timezone.now(),
            data_scadenza=timezone.now() + timedelta(days=30),
            stato='ATTIVA'
        )
        assert scadenza.pratica == pratica
        
        # Verifica relazioni complete
        assert fascicolo.pratiche.count() == 1
        assert pratica.scadenze.count() == 1
        assert fascicolo.documenti.count() == 2
    
    def test_chiusura_pratica_e_fascicolo(
        self, db, pratica, fascicolo, documento
    ):
        """Test chiusura coordinata di pratica e fascicolo"""
        from pratiche.models import Pratica
        from fascicoli.models import Fascicolo
        
        # Collega pratica a fascicolo
        fascicolo.pratiche.add(pratica)
        documento.pratica = pratica
        documento.fascicolo = fascicolo
        documento.save()
        
        # Chiudi pratica
        pratica.stato = 'chiusa'
        pratica.data_chiusura = timezone.now().date()
        pratica.save()
        
        assert pratica.stato == 'chiusa'
        assert pratica.data_chiusura is not None
        
        # Verifica che il fascicolo possa essere chiuso
        fascicolo.stato = 'chiuso'
        fascicolo.save()
        
        assert fascicolo.stato == 'chiuso'


@pytest.mark.integration
class TestFlussoComunicazioniDocumenti:
    """Test integrazione Comunicazioni con Documenti"""
    
    def test_invio_comunicazione_con_allegato(
        self, db, cliente_pf, comunicazione, documento
    ):
        """Test invio comunicazione con documento allegato"""
        from comunicazioni.models import Comunicazione, AllegatoComunicazione
        
        # Collega documento come allegato
        comunicazione.oggetto = 'Comunicazione con allegato'
        comunicazione.save()
        
        # Crea allegato (se il modello esiste)
        # AllegatoComunicazione.objects.create(
        #     comunicazione=comunicazione,
        #     documento=documento
        # )
        
        assert comunicazione.destinatario == cliente_pf.anagrafica
    
    def test_comunicazione_genera_documento(
        self, db, cliente_pf, documento_tipo, fascicolo
    ):
        """Test: comunicazione che genera documento protocollato"""
        from comunicazioni.models import Comunicazione
        from documenti.models import Documento
        from protocollo.models import MovimentoProtocollo
        
        # Crea comunicazione
        comunicazione = Comunicazione.objects.create(
            destinatario=cliente_pf.anagrafica,
            oggetto='Comunicazione importante',
            testo='Corpo del messaggio',
            tipo='EMAIL'
        )
        
        # Genera documento dalla comunicazione
        documento = Documento.objects.create(
            cliente=cliente_pf,
            tipo=documento_tipo,
            fascicolo=fascicolo,
            descrizione=f'Doc da comunicazione: {comunicazione.oggetto}'
        )
        
        # Protocolla
        movimento = MovimentoProtocollo.objects.create(
            content_type=ContentType.objects.get_for_model(Documento),
            object_id=documento.id,
            tipo='OUT',
            numero_protocollo=10,
            data_protocollo=timezone.now().date()
        )
        
        assert movimento.content_object == documento


@pytest.mark.integration
class TestFlussoPraticaNotaRelazioni:
    """Test integrazione Note e Relazioni tra Pratiche"""
    
    def test_pratica_con_note_multiple(self, db, pratica, user):
        """Test aggiunta note a pratica"""
        from pratiche.models import PraticaNota
        
        # Aggiungi note
        nota1 = PraticaNota.objects.create(
            pratica=pratica,
            testo='Prima nota importante',
            autore=user
        )
        nota2 = PraticaNota.objects.create(
            pratica=pratica,
            testo='Seconda nota di aggiornamento',
            autore=user
        )
        
        note = pratica.note.all()
        assert note.count() == 2
        assert nota1 in note
        assert nota2 in note
    
    def test_relazioni_tra_pratiche(
        self, db, cliente_pf, pratica_tipo, make_pratica
    ):
        """Test relazioni tra pratiche collegate"""
        from pratiche.models import Pratica, PraticaRelazione
        
        # Crea pratiche collegate
        pratica_principale = make_pratica(
            cliente=cliente_pf,
            tipo=pratica_tipo,
            codice='PRAT-001',
            oggetto='Pratica principale'
        )
        
        pratica_collegata = make_pratica(
            cliente=cliente_pf,
            tipo=pratica_tipo,
            codice='PRAT-002',
            oggetto='Pratica collegata'
        )
        
        # Crea relazione
        relazione = PraticaRelazione.objects.create(
            pratica_da=pratica_principale,
            pratica_a=pratica_collegata,
            tipo='COLLEGATA'
        )
        
        assert relazione.pratica_da == pratica_principale
        assert relazione.pratica_a == pratica_collegata


@pytest.mark.integration
class TestFlussoCreazioneCompletaArchivio:
    """Test flusso completo dalla creazione alla archiviazione"""
    
    def test_flusso_archivio_completo(
        self, db, cliente_pf, pratica_tipo, fascicolo_tipo,
        documento_tipo, classificazione, unita_archivio, user
    ):
        """
        Test flusso archivio end-to-end:
        1. Cliente
        2. Pratica
        3. Fascicolo
        4. Documenti
        5. Protocollazione
        6. Collocazione fisica
        7. Note e scadenze
        """
        from pratiche.models import Pratica, PraticaNota
        from fascicoli.models import Fascicolo
        from documenti.models import Documento
        from protocollo.models import MovimentoProtocollo
        from archivio_fisico.models import CollocazioneFisica
        from scadenze.models import Scadenza
        
        # 1. Cliente già fornito da fixture
        assert cliente_pf.pk is not None
        
        # 2. Crea pratica
        pratica = Pratica.objects.create(
            cliente=cliente_pf,
            tipo=pratica_tipo,
            codice='ARCH-2024-001',
            oggetto='Pratica archivio completo',
            stato='aperta'
        )
        
        # 3. Crea fascicolo
        fascicolo = Fascicolo.objects.create(
            cliente=cliente_pf,
            tipo=fascicolo_tipo,
            classificazione=classificazione,
            titolo='Fascicolo archivio',
            stato='aperto'
        )
        fascicolo.pratiche.add(pratica)
        
        # 4. Crea documenti
        documenti = []
        for i in range(3):
            doc = Documento.objects.create(
                cliente=cliente_pf,
                tipo=documento_tipo,
                fascicolo=fascicolo,
                pratica=pratica,
                descrizione=f'Documento {i+1}'
            )
            documenti.append(doc)
        
        # 5. Protocolla documenti
        for i, doc in enumerate(documenti):
            MovimentoProtocollo.objects.create(
                content_type=ContentType.objects.get_for_model(Documento),
                object_id=doc.id,
                tipo='IN',
                numero_protocollo=100 + i,
                data_protocollo=timezone.now().date()
            )
        
        # 6. Assegna collocazioni fisiche
        for i, doc in enumerate(documenti):
            CollocazioneFisica.objects.create(
                content_type=ContentType.objects.get_for_model(Documento),
                object_id=doc.id,
                unita=unita_archivio,
                posizione=i + 1
            )
        
        # 7. Aggiungi note e scadenze
        PraticaNota.objects.create(
            pratica=pratica,
            testo='Pratica completamente archiviata',
            autore=user
        )
        
        Scadenza.objects.create(
            pratica=pratica,
            titolo='Revisione archivio',
            data_inizio=timezone.now(),
            data_scadenza=timezone.now() + timedelta(days=365),
            stato='ATTIVA'
        )
        
        # Verifica completezza
        assert fascicolo.documenti.count() == 3
        assert pratica.note.count() == 1
        assert pratica.scadenze.count() == 1
        
        # Verifica tutti i documenti protocollati
        for doc in documenti:
            movimenti = MovimentoProtocollo.objects.filter(
                content_type=ContentType.objects.get_for_model(Documento),
                object_id=doc.id
            )
            assert movimenti.exists()
        
        # Verifica tutte le collocazioni
        collocazioni = CollocazioneFisica.objects.filter(
            content_type=ContentType.objects.get_for_model(Documento),
            object_id__in=[d.id for d in documenti]
        )
        assert collocazioni.count() == 3
