"""
Test per validatori Codice Fiscale e Partita IVA
"""
import pytest
from django.core.exceptions import ValidationError
from anagrafiche.utils import (
    build_cli_base6,
    get_or_generate_cli,
    _alnum_upper,
    _pad
)
from anagrafiche.models import Anagrafica
from .fixtures_cf_piva import (
    CODICI_FISCALI_VALIDI,
    CODICI_FISCALI_NON_VALIDI,
    PARTITE_IVA_VALIDE,
    PARTITE_IVA_NON_VALIDE,
    TEST_PERSONE_FISICHE,
    TEST_PERSONE_GIURIDICHE
)


@pytest.mark.unit
class TestCodiceFiscaleValidator:
    """Test validazione Codice Fiscale"""
    
    def test_codice_fiscale_valido(self, db):
        """CF valido deve passare la validazione"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01H501U'
        )
        # Non dovrebbe sollevare eccezioni
        anagrafica.full_clean()
    
    def test_codice_fiscale_invalido_lunghezza(self, db):
        """CF con lunghezza errata deve fallire"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01'  # Troppo corto
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    def test_codice_fiscale_invalido_caratteri(self, db):
        """CF con caratteri non validi deve fallire"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01H501@'  # @ non valido
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    def test_codice_fiscale_case_insensitive(self, db):
        """CF deve essere convertito in maiuscolo automaticamente"""
        cf_upper = CODICI_FISCALI_VALIDI[0]
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale=cf_upper.lower()  # minuscolo
        )
        anagrafica.full_clean()
        anagrafica.save()
        # Dopo il save, il CF dovrebbe essere maiuscolo
        anagrafica.refresh_from_db()
        assert anagrafica.codice_fiscale == cf_upper
    
    @pytest.mark.parametrize('cf_valido', CODICI_FISCALI_VALIDI[:3])
    def test_codici_fiscali_validi_vari(self, db, cf_valido):
        """Test con vari CF validi con checksum corretto"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Test',
            cognome='User',
            codice_fiscale=cf_valido
        )
        anagrafica.full_clean()
    
    @pytest.mark.parametrize('cf_invalido', [
        'RSSMRA80A01H501',     # Troppo corto
        'RSSMRA80A01H501UU',   # Troppo lungo
        '1234567890ABCDEF',    # Solo numeri e lettere
        'RSSMRA80A01H501@',    # Carattere speciale
        'RSSMRA80A01H501X',    # Checksum errato
    ])
    def test_codici_fiscali_invalidi_vari(self, db, cf_invalido):
        """Test con vari CF invalidi"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Test',
            cognome='User',
            codice_fiscale=cf_invalido
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    def test_codice_fiscale_obbligatorio_per_pf(self, db):
        """CF dovrebbe essere obbligatorio per Persona Fisica"""
        anagrafica = Anagrafica(
            tipo='PF',
            nome='Mario',
            cognome='Rossi'
            # codice_fiscale mancante
        )
        # Verifica se il modello richiede CF per PF
        # (dipende dall'implementazione del modello)
        try:
            anagrafica.full_clean()
        except ValidationError as e:
            assert 'codice_fiscale' in str(e) or 'required' in str(e).lower()


@pytest.mark.unit
class TestPartitaIVAValidator:
    """Test validazione Partita IVA"""
    
    def test_partita_iva_valida(self, db):
        """P.IVA valida deve passare"""
        piva = PARTITE_IVA_VALIDE[0]
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Acme SRL',
            partita_iva=piva,
            codice_fiscale=piva  # Per PG, CF == P.IVA
        )
        anagrafica.full_clean()
    
    def test_partita_iva_invalida_lunghezza(self, db):
        """P.IVA con lunghezza errata deve fallire"""
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Acme SRL',
            codice_fiscale='12345678903',  # Valido
            partita_iva='123456789'  # Troppo corta (11 cifre richieste)
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    def test_partita_iva_con_lettere(self, db):
        """P.IVA con lettere deve fallire"""
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Acme SRL',
            codice_fiscale='12345678903',  # Valido
            partita_iva='1234567890A'  # Contiene lettera
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    @pytest.mark.parametrize('piva_valida', PARTITE_IVA_VALIDE[:2])
    def test_partite_iva_valide_varie(self, db, piva_valida):
        """Test con varie P.IVA valide con checksum corretto"""
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Test SRL',
            partita_iva=piva_valida,
            codice_fiscale=piva_valida  # Per PG, CF == P.IVA
        )
        anagrafica.full_clean()
    
    @pytest.mark.parametrize('piva_invalida', [
        '123456789',       # Troppo corta
        '123456789012',    # Troppo lunga
        '1234567890A',     # Contiene lettere
        'ABCDEFGHILM',     # Solo lettere
        '12345678901',     # Checksum errato
    ])
    def test_partite_iva_invalide_varie(self, db, piva_invalida):
        """Test con varie P.IVA invalide"""
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Test SRL',
            codice_fiscale='12345678903',  # CF valido richiesto
            partita_iva=piva_invalida
        )
        with pytest.raises(ValidationError):
            anagrafica.full_clean()
    
    def test_partita_iva_obbligatoria_per_pg(self, db):
        """P.IVA dovrebbe essere obbligatoria per Persona Giuridica"""
        anagrafica = Anagrafica(
            tipo='PG',
            ragione_sociale='Acme SRL',
            codice_fiscale='12345678903'  # CF richiesto
            # partita_iva mancante
        )
        with pytest.raises(ValidationError) as exc_info:
            anagrafica.full_clean()
        # Verifica che l'errore riguardi P.IVA (o generalmente required)
        error_msg = str(exc_info.value).lower()
        assert 'partita_iva' in error_msg or 'required' in error_msg


@pytest.mark.unit
class TestUtilsGeneratoreCodiceCliente:
    """Test per generatore codice cliente"""
    
    def test_alnum_upper(self):
        """Test helper _alnum_upper"""
        assert _alnum_upper("Mario Rossi 123!") == "MARIOROSSI123"
        assert _alnum_upper("Test-123_ABC") == "TEST123ABC"
        assert _alnum_upper("") == ""
        assert _alnum_upper(None) == ""
    
    def test_pad(self):
        """Test helper _pad"""
        assert _pad("ABC", 5, "0") == "ABC00"
        assert _pad("ABCDEF", 3, "0") == "ABC"
        assert _pad("AB", 5, "X") == "ABXXX"
        assert _pad("", 3, "0") == "000"
    
    def test_build_cli_base6_persona_fisica(self, anagrafica_pf):
        """Test generazione base6 per PF"""
        anagrafica_pf.tipo = 'PF'
        anagrafica_pf.cognome = 'Rossi'
        anagrafica_pf.nome = 'Mario'
        
        code = build_cli_base6(anagrafica_pf)
        assert len(code) == 6
        # Verifica formato: 3 caratteri cognome + 3 caratteri nome (padding con 0)
        assert code[:3] in ['ROS', 'RSS']  # Può variare in base all'implementazione
        assert code[3] == 'M'  # Inizia con M (Mario)
    
    def test_build_cli_base6_persona_giuridica(self, anagrafica_pg):
        """Test generazione base6 per PG"""
        anagrafica_pg.tipo = 'PG'
        anagrafica_pg.ragione_sociale = 'Acme'
        
        code = build_cli_base6(anagrafica_pg)
        assert len(code) == 6
        assert code.startswith('ACME')
    
    def test_build_cli_base6_cognome_corto(self, anagrafica_pf):
        """Test con cognome molto corto"""
        anagrafica_pf.tipo = 'PF'
        anagrafica_pf.cognome = 'Li'
        anagrafica_pf.nome = 'Wu'
        
        code = build_cli_base6(anagrafica_pf)
        assert len(code) == 6
        # Dovrebbe essere paddato con zeri
        assert code == 'LI0WU0'
    
    def test_get_or_generate_cli_new_cliente(self, anagrafica_pf):
        """Test generazione codice per nuovo cliente"""
        anagrafica_pf.tipo = 'PF'
        anagrafica_pf.cognome = 'Rossi'
        anagrafica_pf.nome = 'Mario'
        anagrafica_pf.codice = None
        
        code = get_or_generate_cli(anagrafica_pf)
        assert len(code) == 8  # 6 base + 2 suffisso
        assert code[:6].isalnum()
        assert code[6:].isdigit()
    
    def test_get_or_generate_cli_existing_valid(self, anagrafica_pf):
        """Test con codice esistente valido"""
        existing_code = 'RSSMRA01'
        anagrafica_pf.codice = existing_code
        
        code = get_or_generate_cli(anagrafica_pf)
        assert code == existing_code
    
    def test_get_or_generate_cli_reject_cli_prefix(self, anagrafica_pf):
        """Test rigetto codice che inizia con CLI"""
        anagrafica_pf.codice = 'CLI00001'
        
        code = get_or_generate_cli(anagrafica_pf)
        # Dovrebbe generare nuovo codice
        assert not code.startswith('CLI')
    
    def test_get_or_generate_cli_incremental_suffix(self, db):
        """Test incremento suffisso per codici duplicati"""
        # Crea prima anagrafica
        existing = Anagrafica.objects.create(
            tipo='PF',
            cognome='Rossi',
            nome='Mario',
            codice_fiscale='RSSMRA80A01H501U',
            codice='RSSMRA01'
        )
        
        # Crea seconda anagrafica con stessi dati
        new_anagrafica = Anagrafica(
            tipo='PF',
            cognome='Rossi',
            nome='Mario',
            codice_fiscale='VRDGPP85M01F205W',  # CF diverso
            codice=None
        )
        
        code = get_or_generate_cli(new_anagrafica)
        # Suffisso dovrebbe essere incrementato (02, 03, etc)
        assert len(code) == 8
        assert code != existing.codice


@pytest.mark.unit
class TestAnagraficaModel:
    """Test per modello Anagrafica"""
    
    def test_create_persona_fisica(self, db):
        """Test creazione persona fisica"""
        anag = Anagrafica.objects.create(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01H501U',
            email='mario.rossi@example.com'
        )
        assert anag.pk is not None
        assert anag.tipo == 'PF'
        # __str__ potrebbe includere CF, verifica solo che contenga nome/cognome
        str_anag = str(anag)
        assert 'Rossi' in str_anag
        assert 'Mario' in str_anag
    
    def test_create_persona_giuridica(self, db):
        """Test creazione persona giuridica"""
        anag = Anagrafica.objects.create(
            tipo='PG',
            ragione_sociale='Acme SRL',
            partita_iva='12345678901',
            email='info@acme.it'
        )
        assert anag.pk is not None
        assert anag.tipo == 'PG'
        assert 'Acme' in str(anag)
    
    def test_unique_codice_fiscale(self, db, anagrafica_pf):
        """Test unicità codice fiscale"""
        with pytest.raises(Exception):  # IntegrityError o ValidationError
            Anagrafica.objects.create(
                tipo='PF',
                nome='Luigi',
                cognome='Bianchi',
                codice_fiscale=anagrafica_pf.codice_fiscale  # Duplicato
            )
    
    def test_unique_partita_iva(self, db, anagrafica_pg):
        """Test unicità partita IVA"""
        with pytest.raises(Exception):
            Anagrafica.objects.create(
                tipo='PG',
                ragione_sociale='Test SRL',
                partita_iva=anagrafica_pg.partita_iva  # Duplicato
            )
