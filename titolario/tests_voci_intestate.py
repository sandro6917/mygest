"""
Test per funzionalità voci titolario intestate ad anagrafiche
"""
import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica


@pytest.mark.django_db
class TestVociIntestate:
    """Test per voci titolario intestate ad anagrafiche"""
    
    def test_creazione_voce_base_con_flag_intestazione(self):
        """Test: voce base può avere consente_intestazione=True"""
        voce = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier personale',
            consente_intestazione=True
        )
        
        assert voce.consente_intestazione is True
        assert voce.anagrafica is None
        assert voce.is_voce_intestata() is False
    
    def test_creazione_voce_intestata_ad_anagrafica(self):
        """Test: creazione voce intestata ad anagrafica"""
        # Crea voce parent con flag
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier personale',
            consente_intestazione=True
        )
        
        # Crea anagrafica
        anagrafica = baker.make(
            'anagrafiche.Anagrafica',
            codice='ROSMAR01',
            nome='Mario',
            cognome='Rossi',
            tipo='PF'
        )
        
        # Crea voce intestata
        voce_intestata = TitolarioVoce.objects.create(
            codice='ROSMAR01',
            titolo='Mario Rossi',
            parent=parent,
            anagrafica=anagrafica,
            pattern_codice='{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}'
        )
        
        assert voce_intestata.anagrafica == anagrafica
        assert voce_intestata.parent == parent
        assert voce_intestata.is_voce_intestata() is True
        assert 'Mario' in str(voce_intestata)
    
    def test_validazione_parent_deve_consentire_intestazione(self):
        """Test: parent deve avere consente_intestazione=True"""
        # Parent senza flag
        parent = TitolarioVoce.objects.create(
            codice='HR',
            titolo='Risorse Umane',
            consente_intestazione=False
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='TEST01')
        
        # Tentativo di creare voce intestata sotto parent che non consente
        voce_intestata = TitolarioVoce(
            codice='TEST01',
            titolo='Test',
            parent=parent,
            anagrafica=anagrafica
        )
        
        with pytest.raises(ValidationError) as exc_info:
            voce_intestata.full_clean()
        
        assert 'non consente voci intestate' in str(exc_info.value)
    
    def test_validazione_voce_intestata_senza_parent(self):
        """Test: voce intestata deve avere un parent"""
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='TEST01')
        
        voce = TitolarioVoce(
            codice='TEST01',
            titolo='Test',
            parent=None,  # Nessun parent
            anagrafica=anagrafica
        )
        
        with pytest.raises(ValidationError) as exc_info:
            voce.full_clean()
        
        assert 'deve avere un parent' in str(exc_info.value)
    
    def test_validazione_voce_non_puo_consentire_e_essere_intestata(self):
        """Test: voce non può contemporaneamente consentire intestazione ed essere intestata"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='TEST01')
        
        voce = TitolarioVoce(
            codice='TEST01',
            titolo='Test',
            parent=parent,
            anagrafica=anagrafica,
            consente_intestazione=True  # Conflitto!
        )
        
        with pytest.raises(ValidationError) as exc_info:
            voce.full_clean()
        
        assert 'contemporaneamente' in str(exc_info.value)
    
    def test_validazione_unicita_anagrafica_per_parent(self):
        """Test: non si possono creare due voci intestate alla stessa anagrafica sotto lo stesso parent"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='ROSMAR01')
        
        # Prima voce intestata
        TitolarioVoce.objects.create(
            codice='ROSMAR01',
            titolo='Mario Rossi',
            parent=parent,
            anagrafica=anagrafica
        )
        
        # Tentativo di creare seconda voce con stessa anagrafica
        voce2 = TitolarioVoce(
            codice='ROSMAR01-BIS',
            titolo='Mario Rossi (duplicato)',
            parent=parent,
            anagrafica=anagrafica
        )
        
        with pytest.raises(ValidationError) as exc_info:
            voce2.full_clean()
        
        assert 'Esiste già una voce intestata' in str(exc_info.value)
    
    def test_get_anagrafiche_disponibili(self):
        """Test: metodo get_anagrafiche_disponibili ritorna anagrafiche non ancora usate"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        # Crea 3 anagrafiche
        ana1 = baker.make('anagrafiche.Anagrafica', codice='ANA01')
        ana2 = baker.make('anagrafiche.Anagrafica', codice='ANA02')
        ana3 = baker.make('anagrafiche.Anagrafica', codice='ANA03')
        
        # Intesta voce alla prima anagrafica
        TitolarioVoce.objects.create(
            codice='ANA01',
            titolo='Ana 1',
            parent=parent,
            anagrafica=ana1
        )
        
        # Verifica disponibili
        disponibili = parent.get_anagrafiche_disponibili()
        assert ana1 not in disponibili
        assert ana2 in disponibili
        assert ana3 in disponibili
    
    def test_codice_gerarchico_con_voce_intestata(self):
        """Test: codice_gerarchico include codice anagrafica"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='ROSMAR01')
        
        voce_intestata = TitolarioVoce.objects.create(
            codice='ROSMAR01',
            titolo='Mario Rossi',
            parent=parent,
            anagrafica=anagrafica
        )
        
        # Crea sotto-voce
        sottovoce = TitolarioVoce.objects.create(
            codice='BUSTE-PAGA',
            titolo='Buste Paga',
            parent=voce_intestata
        )
        
        assert sottovoce.codice_gerarchico() == 'HR-PERS/ROSMAR01/BUSTE-PAGA'
    
    def test_on_delete_protect_anagrafica(self):
        """Test: cancellazione anagrafica bloccata se ha voci titolario"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='ROSMAR01')
        
        TitolarioVoce.objects.create(
            codice='ROSMAR01',
            titolo='Mario Rossi',
            parent=parent,
            anagrafica=anagrafica
        )
        
        # Tentativo di cancellare anagrafica
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            anagrafica.delete()
    
    def test_pattern_codice_con_placeholder_ana(self):
        """Test: pattern_codice può usare {ANA} per codice anagrafica"""
        parent = TitolarioVoce.objects.create(
            codice='HR-PERS',
            titolo='Dossier',
            consente_intestazione=True
        )
        
        anagrafica = baker.make('anagrafiche.Anagrafica', codice='ROSMAR01')
        
        voce_intestata = TitolarioVoce.objects.create(
            codice='ROSMAR01',
            titolo='Mario Rossi',
            parent=parent,
            anagrafica=anagrafica,
            pattern_codice='{CLI}-{ANA}-{TIT}-{SEQ:04d}'
        )
        
        assert '{ANA}' in voce_intestata.pattern_codice
        # Nota: il pattern verrà poi usato in fascicoli.models per generare codici
