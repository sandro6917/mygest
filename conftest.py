"""
Configurazione pytest globale e fixtures comuni
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker
from rest_framework.test import APIClient

User = get_user_model()


# ====================================
# CONFIGURAZIONE TEST (AUTO-APPLY)
# ====================================

@pytest.fixture(autouse=True)
def test_settings(settings, tmp_path):
    """Configurazione automatica per tutti i test"""
    # Disabilita compressione static files
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_OFFLINE = False
    settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    
    # Usa DefaultParser per Redis (non richiede hiredis)
    if 'default' in settings.CACHES:
        settings.CACHES['default']['OPTIONS']['PARSER_CLASS'] = 'redis.connection.DefaultParser'
    
    # Usa temp directory per archivio in test (evita Permission denied su /mnt/archivio)
    test_archivio = tmp_path / "archivio"
    test_archivio.mkdir(exist_ok=True)
    settings.ARCHIVIO_BASE_PATH = str(test_archivio)
    settings.MEDIA_ROOT = str(test_archivio)
    
    return settings


@pytest.fixture
def mock_clamav(monkeypatch):
    """Mock ClamAV per test antivirus senza richiedere ClamAV installato"""
    try:
        import pyclamd
        
        def fake_scan_stream(content):
            """Simula scan ClamAV - sempre pulito"""
            return {'stream': ('OK', None)}
        
        def fake_ping():
            """Simula ping ClamAV - sempre disponibile"""
            return True
        
        # Mock dei metodi ClamAV
        monkeypatch.setattr('pyclamd.ClamdUnixSocket.scan_stream', fake_scan_stream)
        monkeypatch.setattr('pyclamd.ClamdUnixSocket.ping', fake_ping)
        
        # Mock anche per ClamdNetwork se usato
        monkeypatch.setattr('pyclamd.ClamdNetworkSocket.scan_stream', fake_scan_stream)
        monkeypatch.setattr('pyclamd.ClamdNetworkSocket.ping', fake_ping)
        
    except ImportError:
        # pyclamd non installato, skip
        pass
    
    return True


# ====================================
# FIXTURES - USERS & AUTH
# ====================================

@pytest.fixture
def user(db):
    """Utente standard per test"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def superuser(db):
    """Superuser per test admin"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def staff_user(db):
    """Staff user per test con permessi limitati"""
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123'
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    """Client già autenticato"""
    client.force_login(user)
    return client


@pytest.fixture
def api_client():
    """DRF API client"""
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API client già autenticato"""
    api_client.force_authenticate(user=user)
    return api_client


# ====================================
# FIXTURES - ANAGRAFICHE
# ====================================

@pytest.fixture
def anagrafica_pf(db):
    """Anagrafica persona fisica"""
    from anagrafiche.models import Anagrafica
    return baker.make(
        Anagrafica,
        tipo='PF',
        nome='Mario',
        cognome='Rossi',
        codice_fiscale='RSSMRA80A01H501U',
        email='mario.rossi@example.com'
    )


@pytest.fixture
def anagrafica_pg(db):
    """Anagrafica persona giuridica"""
    from anagrafiche.models import Anagrafica
    return baker.make(
        Anagrafica,
        tipo='PG',
        ragione_sociale='Acme SRL',
        partita_iva='12345678901',
        email='info@acme.it'
    )


@pytest.fixture
def cliente_pf(db, anagrafica_pf):
    """Cliente persona fisica"""
    from anagrafiche.models import Cliente
    return baker.make(
        Cliente,
        anagrafica=anagrafica_pf
    )


@pytest.fixture
def cliente_pg(db, anagrafica_pg):
    """Cliente persona giuridica"""
    from anagrafiche.models import Cliente
    return baker.make(
        Cliente,
        anagrafica=anagrafica_pg
    )


# ====================================
# FIXTURES - TITOLARIO & CLASSIFICAZIONE
# ====================================

@pytest.fixture
def titolario_base(db):
    """Titolario di base"""
    from titolario.models import Titolario
    return baker.make(
        Titolario,
        codice='01',
        descrizione='Amministrazione',
        livello=1
    )


@pytest.fixture
def classificazione(db, titolario_base):
    """Classificazione collegata a titolario"""
    from titolario.models import Classificazione
    return baker.make(
        Classificazione,
        titolo=titolario_base,
        anno=2024
    )


# ====================================
# FIXTURES - PRATICHE
# ====================================

@pytest.fixture
def pratica_tipo(db):
    """Tipo pratica"""
    from pratiche.models import PraticheTipo
    return baker.make(
        PraticheTipo,
        codice='GENERICO',
        nome='Pratica Generica'
    )


@pytest.fixture
def pratica(db, cliente_pf, pratica_tipo):
    """Pratica di test"""
    from pratiche.models import Pratica
    return baker.make(
        Pratica,
        cliente=cliente_pf,
        tipo=pratica_tipo,
        codice='PRAT-001',
        oggetto='Pratica di test',
        stato='aperta'
    )


# ====================================
# FIXTURES - FASCICOLI
# ====================================

@pytest.fixture
def fascicolo_tipo(db):
    """Tipo fascicolo"""
    from fascicoli.models import FascicoloTipo
    return baker.make(
        FascicoloTipo,
        nome='Fascicolo Standard'
    )


@pytest.fixture
def fascicolo(db, cliente_pf, fascicolo_tipo, classificazione):
    """Fascicolo di test"""
    from fascicoli.models import Fascicolo
    return baker.make(
        Fascicolo,
        cliente=cliente_pf,
        tipo=fascicolo_tipo,
        classificazione=classificazione,
        titolo='Fascicolo di test',
        stato='aperto'
    )


# ====================================
# FIXTURES - DOCUMENTI
# ====================================

@pytest.fixture
def documento_tipo(db):
    """Tipo documento"""
    from documenti.models import DocumentiTipo
    return baker.make(
        DocumentiTipo,
        codice='GEN',
        nome='Documento Generico'
    )


@pytest.fixture
def documento(db, cliente_pf, documento_tipo, fascicolo):
    """Documento di test"""
    from documenti.models import Documento
    return baker.make(
        Documento,
        cliente=cliente_pf,
        tipo=documento_tipo,
        fascicolo=fascicolo,
        descrizione='Documento di test'
    )


# ====================================
# FIXTURES - PROTOCOLLO
# ====================================

@pytest.fixture
def movimento_protocollo(db, documento):
    """Movimento protocollo"""
    from protocollo.models import MovimentoProtocollo
    from django.contrib.contenttypes.models import ContentType
    
    return baker.make(
        MovimentoProtocollo,
        content_type=ContentType.objects.get_for_model(documento),
        object_id=documento.id,
        tipo='IN',
        numero_protocollo=1
    )


# ====================================
# FIXTURES - SCADENZE
# ====================================

@pytest.fixture
def scadenza(db, pratica):
    """Scadenza di test"""
    from scadenze.models import Scadenza
    from django.utils import timezone
    from datetime import timedelta
    
    return baker.make(
        Scadenza,
        pratica=pratica,
        titolo='Scadenza test',
        data_inizio=timezone.now(),
        data_scadenza=timezone.now() + timedelta(days=30),
        stato='ATTIVA'
    )


# ====================================
# FIXTURES - ARCHIVIO FISICO
# ====================================

@pytest.fixture
def unita_archivio(db):
    """Unità archivio"""
    from archivio_fisico.models import UnitaFisica
    return baker.make(
        UnitaFisica,
        codice='U001',
        descrizione='Unità test',
        tipo='SCATOLA'
    )


@pytest.fixture
def collocazione(db, documento, unita_archivio):
    """Collocazione fisica"""
    from archivio_fisico.models import CollocazioneFisica
    from django.contrib.contenttypes.models import ContentType
    
    return baker.make(
        CollocazioneFisica,
        content_type=ContentType.objects.get_for_model(documento),
        object_id=documento.id,
        unita=unita_archivio,
        posizione=1
    )


# ====================================
# FIXTURES - COMUNICAZIONI
# ====================================

@pytest.fixture
def comunicazione(db, cliente_pf):
    """Comunicazione di test"""
    from comunicazioni.models import Comunicazione
    return baker.make(
        Comunicazione,
        destinatario=cliente_pf.anagrafica,
        oggetto='Test comunicazione',
        testo='Corpo del messaggio di test',
        tipo='EMAIL'
    )


# ====================================
# HELPERS
# ====================================

@pytest.fixture
def make_anagrafica(db):
    """Factory per creare anagrafiche al volo"""
    def _make(**kwargs):
        from anagrafiche.models import Anagrafica
        return baker.make(Anagrafica, **kwargs)
    return _make


@pytest.fixture
def make_documento(db):
    """Factory per creare documenti al volo"""
    def _make(**kwargs):
        from documenti.models import Documento
        return baker.make(Documento, **kwargs)
    return _make


@pytest.fixture
def make_pratica(db):
    """Factory per creare pratiche al volo"""
    def _make(**kwargs):
        from pratiche.models import Pratica
        return baker.make(Pratica, **kwargs)
    return _make


# ====================================
# SETTINGS OVERRIDES
# ====================================

@pytest.fixture
def settings_with_cache(settings):
    """Settings con cache attiva per test"""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }
    return settings


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Abilita accesso al database per tutti i test"""
    pass


# ====================================
# MARKERS
# ====================================

def pytest_configure(config):
    """Configurazione markers personalizzati"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
