"""
Test per la sanitizzazione automatica dei nomi file.
Verifica che i caratteri non validi vengano rimossi o sostituiti.
"""
import pytest
from model_bakery import baker
from documenti.models import DocumentiTipo, Documento, AttributoDefinizione, AttributoValore
from documenti.utils import build_document_filename, _sanitize_filename_part


@pytest.mark.django_db
class TestFilenameSanitization:
    """Test sanitizzazione caratteri non validi nei nomi file."""

    def test_sanitize_slash(self):
        """Verifica che gli slash / vengano sostituiti con trattino."""
        assert _sanitize_filename_part("06/2025") == "06-2025"
        assert _sanitize_filename_part("test/file/name") == "test-file-name"

    def test_sanitize_backslash(self):
        """Verifica che i backslash \\ vengano sostituiti con trattino."""
        assert _sanitize_filename_part("test\\file") == "test-file"

    def test_sanitize_colon(self):
        """Verifica che i due punti : vengano sostituiti."""
        assert _sanitize_filename_part("file:name") == "file-name"

    def test_sanitize_asterisk(self):
        """Verifica che gli asterischi * vengano sostituiti."""
        assert _sanitize_filename_part("file*name") == "file-name"

    def test_sanitize_question_mark(self):
        """Verifica che i punti interrogativi ? vengano sostituiti."""
        assert _sanitize_filename_part("file?name") == "file-name"

    def test_sanitize_quotes(self):
        """Verifica che le virgolette vengano sostituite."""
        assert _sanitize_filename_part('file"name') == "file-name"

    def test_sanitize_angle_brackets(self):
        """Verifica che < e > vengano sostituiti."""
        assert _sanitize_filename_part("file<name>") == "file-name-"

    def test_sanitize_pipe(self):
        """Verifica che il pipe | venga sostituito."""
        assert _sanitize_filename_part("file|name") == "file-name"

    def test_sanitize_multiple_underscores(self):
        """Verifica che trattini multipli vengano ridotti a uno."""
        result = _sanitize_filename_part("file//name**test")
        assert "--" not in result
        assert result == "file-name-test"

    def test_sanitize_empty_string(self):
        """Verifica che stringa vuota resti vuota."""
        assert _sanitize_filename_part("") == ""
        assert _sanitize_filename_part(None) == ""

    def test_documento_arinps_con_periodo_slash(self):
        """Test completo: documento ARINPS con periodo contenente slash."""
        # Crea tipo documento
        tipo = baker.make(
            DocumentiTipo,
            codice="ARINPS",
            nome="Avviso di rettifica INPS",
            nome_file_pattern="RettificaINPS_{attr:modello}_{attr:periodo}_{attr:matricola}_{cliente.anagrafica.codice}",
        )

        # Crea attributi
        attr_modello = baker.make(
            AttributoDefinizione,
            tipo_documento=tipo,
            codice="modello",
            nome="Modello",
            tipo_dato="string",
        )
        attr_periodo = baker.make(
            AttributoDefinizione,
            tipo_documento=tipo,
            codice="periodo",
            nome="Periodo",
            tipo_dato="string",
            regex=r'^(0[1-9]|1[0-2])/?[0-9]{4}$',
        )
        attr_matricola = baker.make(
            AttributoDefinizione,
            tipo_documento=tipo,
            codice="matricola",
            nome="Matricola",
            tipo_dato="string",
        )

        # Crea cliente con anagrafica
        from anagrafiche.models import Anagrafica, Cliente
        anagrafica = baker.make(
            Anagrafica,
            codice="TESTCLI01",
            codice_fiscale="12345678901",
        )
        cliente = baker.make(Cliente, anagrafica=anagrafica)

        # Crea documento
        documento = baker.make(
            Documento,
            tipo=tipo,
            cliente=cliente,
            descrizione="Test documento",
        )

        # Valorizza attributi (incluso periodo con slash)
        baker.make(
            AttributoValore,
            documento=documento,
            definizione=attr_modello,
            valore="DM-2013",
        )
        baker.make(
            AttributoValore,
            documento=documento,
            definizione=attr_periodo,
            valore="06/2025",  # Contiene slash!
        )
        baker.make(
            AttributoValore,
            documento=documento,
            definizione=attr_matricola,
            valore="3601978802",
        )

        # Genera nome file
        filename = build_document_filename(documento, "original.pdf")

        # Verifica che non contenga slash
        assert "/" not in filename, f"Il nome file contiene slash: {filename}"
        assert "\\" not in filename, f"Il nome file contiene backslash: {filename}"

        # Verifica formato atteso
        assert filename == "RettificaINPS_DM-2013_06-2025_3601978802_TESTCLI01.pdf"

    def test_attributo_con_caratteri_speciali_multipli(self):
        """Test con attributo contenente vari caratteri non validi."""
        tipo = baker.make(
            DocumentiTipo,
            codice="TEST",
            nome_file_pattern="Doc_{attr:test_attr}",
        )

        attr = baker.make(
            AttributoDefinizione,
            tipo_documento=tipo,
            codice="test_attr",
            nome="Test",
            tipo_dato="string",
        )

        from anagrafiche.models import Anagrafica, Cliente
        cliente = baker.make(Cliente, anagrafica=baker.make(Anagrafica))

        documento = baker.make(Documento, tipo=tipo, cliente=cliente)

        # Valore con molti caratteri non validi
        baker.make(
            AttributoValore,
            documento=documento,
            definizione=attr,
            valore="test/file\\name:2025*?",
        )

        filename = build_document_filename(documento, "test.pdf")

        # Tutti i caratteri speciali dovrebbero essere sostituiti
        assert "/" not in filename
        assert "\\" not in filename
        assert ":" not in filename
        assert "*" not in filename
        assert "?" not in filename

        # Il nome dovrebbe essere sanitizzato
        assert "test-file-name-2025" in filename

    def test_cliente_anagrafica_codice_con_caratteri_speciali(self):
        """Test che il codice anagrafica venga sanitizzato."""
        tipo = baker.make(
            DocumentiTipo,
            codice="TEST",
            nome_file_pattern="Doc_{cliente.anagrafica.codice}",
        )

        from anagrafiche.models import Anagrafica, Cliente
        # Codice con caratteri speciali (improbabile ma possibile)
        anagrafica = baker.make(Anagrafica, codice="CLI/001")
        cliente = baker.make(Cliente, anagrafica=anagrafica)

        documento = baker.make(Documento, tipo=tipo, cliente=cliente)

        filename = build_document_filename(documento, "test.pdf")

        # Lo slash dovrebbe essere stato sostituito
        assert "/" not in filename
        assert "CLI-001" in filename
