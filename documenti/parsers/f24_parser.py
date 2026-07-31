"""
Parser per Modelli F24 (versamenti unificati Agenzia Entrate).

Estrae i dati necessari all'importazione automatica nel sistema:
data di scadenza della rata e codice fiscale/partita IVA del contribuente.

Nota: nei PDF F24 generati da molti software gestionali, le etichette statiche
del modulo (es. "CODICE FISCALE", "SEZIONE ERARIO") fanno parte di un'immagine
di sfondo e NON sono incluse nel testo estraibile via pdfplumber — solo i valori
compilati lo sono. L'estrazione si basa quindi sulla forma dei dati (formato
codice fiscale/partita IVA) più che su etichette testuali, con l'etichetta come
fallback per layout che invece la includono.
"""
from __future__ import annotations

import re
from typing import TypedDict, Optional
from datetime import datetime

import pdfplumber


class F24ParseResult(TypedDict):
    """Dati estratti dal Modello F24"""
    codice_fiscale: str
    data_scadenza: Optional[str]  # None se il modulo non riporta una scadenza
    denominazione: Optional[str]
    importo_saldo: Optional[str]  # totale della delega (SALDO FINALE)


# Codice fiscale persona fisica: 6 lettere + 2 cifre + 1 lettera + 2 cifre + 1 lettera + 3 cifre + 1 lettera
# Tollera spazi tra i singoli caratteri (caselle del modulo estratte come cifre/lettere separate)
_CF_PERSONA_FISICA = (
    r'(?:[A-Z][ \t]*){6}(?:\d[ \t]*){2}[A-Z][ \t]*(?:\d[ \t]*){2}[A-Z][ \t]*(?:\d[ \t]*){3}[A-Z][ \t]*'
)
# Partita IVA / codice fiscale persona giuridica: 11 cifre
_PIVA = r'(?:\d[ \t]*){11}'

_CF_O_PIVA_PATTERN = re.compile(
    r'(' + _CF_PERSONA_FISICA + r'|' + _PIVA + r')',
    re.IGNORECASE,
)


def _extract_field(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Helper per estrarre un campo con regex"""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if match:
        value = match.group(group).strip()
        return value if value and value != "-" else None
    return None


def _parse_data_italiana(data_raw: Optional[str]) -> Optional[str]:
    """
    Converte una data italiana (formato gg/mm/aaaa, gg-mm-aaaa oppure gg.mm.aaaa,
    a seconda del software che ha generato l'F24: i separatori usati variano)
    in formato ISO YYYY-MM-DD, la rappresentazione usata per i campi data in
    tutto il sistema (coerente con gli altri parser/importer, es. UNILAV/cedolini).
    """
    if not data_raw:
        return None
    normalizzata = data_raw.replace('-', '/').replace('.', '/')
    try:
        return datetime.strptime(normalizzata, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _extract_codice_fiscale(text: str) -> Optional[str]:
    """
    Estrae il codice fiscale/P.IVA del contribuente.

    Nel layout standard del modulo F24 il codice fiscale del contribuente è il
    primo token in questo formato che compare nel testo (precede sempre il
    "codice atto"/altri codici numerici a 11 cifre più in basso nel modulo,
    es. nella sezione erario), quindi si usa il primo match (leftmost) trovato
    nell'intero testo. Prova prima con l'etichetta esplicita "CODICE FISCALE"
    (presente in alcuni layout), poi senza etichetta.
    """
    match = re.search(
        r'CODICE\s+FISCALE[ \t]*\n?(' + _CF_PERSONA_FISICA + r'|' + _PIVA + r')',
        text,
        re.IGNORECASE,
    )
    if not match:
        match = _CF_O_PIVA_PATTERN.search(text)

    if not match:
        return None

    return re.sub(r'\s+', '', match.group(1)).upper()


def _extract_importo_saldo(text: str) -> Optional[str]:
    """
    Estrae il totale della delega (SALDO FINALE) del modulo F24.

    Prova prima l'etichetta esplicita "SALDO FINALE" (presente in alcuni
    layout); se assente (etichette del modulo non incluse nel testo, come nel
    layout più comune), usa in fallback l'ultimo importo in formato italiano
    presente nel testo — nel modulo F24 il saldo finale è sempre l'ultimo
    importo riportato, prima degli estremi di versamento (che non contengono
    importi in questo formato). Tollera spazi interni tra cifre/virgola
    (alcuni layout con caselle per singola cifra estraggono es. "93, 73"
    invece di "93,73").
    """
    importo_pattern = r'\d{1,3}(?:\.\d{3})*,[ \t]*\d[ \t]*\d'

    match = re.search(r'SALDO\s+FINALE\s*\n?[^\d\-]*(' + importo_pattern + r')', text, re.IGNORECASE)
    if match:
        return re.sub(r'[ \t]+', '', match.group(1))

    importi = re.findall(importo_pattern, text)
    return re.sub(r'[ \t]+', '', importi[-1]) if importi else None



def parse_f24_pdf(pdf_path: str) -> F24ParseResult:
    """
    Estrae dati strutturati da un PDF Modello F24.

    Args:
        pdf_path: Percorso del file PDF da analizzare

    Returns:
        Dizionario con codice fiscale, data scadenza e dati opzionali

    Raises:
        ValueError: Se il PDF non è un valido Modello F24
        FileNotFoundError: Se il file non esiste
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("Il PDF è vuoto")

            full_text = ""
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n\n"

            if not full_text.strip():
                raise ValueError(
                    "Impossibile estrarre testo dal PDF "
                    "(documento scansionato senza livello testo?)"
                )

            # Layout diversi usano etichette diverse ("Scadenza rata:", "Scadenza del",
            # semplice "SCADENZA") e separatori diversi ("/", "-" o "."): tutti tollerati.
            # Non tutti i modelli F24 riportano una scadenza (es. versamenti in unica
            # soluzione senza rateazione): in tal caso il valore resta None, non è un errore.
            data_scadenza_raw = _extract_field(full_text, r'Scadenza\s*(?:rata|del)?\s*:?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})')
            if not data_scadenza_raw:
                data_scadenza_raw = _extract_field(full_text, r'data\s+scadenza[\s\S]{0,10}?(\d{2}[/\-.]\d{2}[/\-.]\d{4})')

            data_scadenza = _parse_data_italiana(data_scadenza_raw)

            codice_fiscale = _extract_codice_fiscale(full_text)
            if not codice_fiscale:
                raise ValueError("Codice fiscale contribuente non trovato: il documento non sembra un Modello F24 valido")

            # Best-effort: in alcuni layout il valore non segue direttamente
            # l'etichetta nel testo estratto, e il match cattura per errore la
            # parola residua dell'etichetta stessa (es. "nome"): scartata.
            denominazione = _extract_field(
                full_text,
                r'(?:cognome,?\s*denominazione\s+o\s+ragione\s+sociale)\s*\n?(.+?)(?:\n|$)',
            )
            if denominazione and denominazione.strip().lower() in {'nome', 'cognome', 'denominazione', 'ragione sociale'}:
                denominazione = None

            importo_saldo = _extract_importo_saldo(full_text)

            return {
                "codice_fiscale": codice_fiscale,
                "data_scadenza": data_scadenza,
                "denominazione": denominazione,
                "importo_saldo": importo_saldo,
            }

    except FileNotFoundError:
        raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Errore durante il parsing del PDF: {str(e)}")
