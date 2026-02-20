"""
Parser per documenti UNILAV (Comunicazioni Obbligatorie Lavoro)

Estrae dati strutturati da PDF UNILAV per l'importazione automatica nel sistema.
Supporta formati UNILAV 2021 e versioni successive.
"""
from __future__ import annotations
import re
from typing import TypedDict, Optional
from datetime import datetime
import pdfplumber


class DatoreLavoroData(TypedDict):
    """Dati estratti del datore di lavoro"""
    codice_fiscale: str
    denominazione: str
    settore: Optional[str]
    comune_sede_legale: Optional[str]
    cap_sede_legale: Optional[str]
    indirizzo_sede_legale: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    comune_sede_lavoro: Optional[str]
    cap_sede_lavoro: Optional[str]
    indirizzo_sede_lavoro: Optional[str]
    

class LavoratoreData(TypedDict):
    """Dati estratti del lavoratore"""
    codice_fiscale: str
    cognome: str
    nome: str
    sesso: Optional[str]
    data_nascita: Optional[str]
    comune_nascita: Optional[str]
    cittadinanza: Optional[str]
    comune_domicilio: Optional[str]
    cap_domicilio: Optional[str]
    indirizzo_domicilio: Optional[str]
    livello_istruzione: Optional[str]


class UnilavData(TypedDict):
    """Dati estratti dal documento UNILAV"""
    codice_comunicazione: str
    tipo_comunicazione: str
    modello: Optional[str]
    data_comunicazione: str
    centro_impiego: Optional[str]
    provincia_impiego: Optional[str]
    data_inizio_rapporto: Optional[str]
    data_fine_rapporto: Optional[str]
    data_proroga: Optional[str]
    data_trasformazione: Optional[str]  # Data trasformazione (per tipo Trasformazione)
    causa_trasformazione: Optional[str]  # Motivo trasformazione
    ente_previdenziale: Optional[str]
    codice_ente_previdenziale: Optional[str]
    pat_inail: Optional[str]
    tipologia_contrattuale: Optional[str]
    tipo_orario: Optional[str]
    ore_settimanali: Optional[str]
    qualifica_professionale: Optional[str]
    contratto_collettivo: Optional[str]
    livello_inquadramento: Optional[str]
    retribuzione: Optional[str]
    giornate_lavorative: Optional[str]
    soggetto_comunicazione: Optional[str]
    cf_soggetto_comunicazione: Optional[str]


class UnilavParseResult(TypedDict):
    """Risultato completo del parsing"""
    datore: DatoreLavoroData
    lavoratore: LavoratoreData
    unilav: UnilavData


def parse_unilav_pdf(pdf_path: str) -> UnilavParseResult:
    """
    Estrae dati strutturati da un PDF UNILAV.
    
    Args:
        pdf_path: Percorso del file PDF da analizzare
        
    Returns:
        Dizionario con dati di datore, lavoratore e documento
        
    Raises:
        ValueError: Se il PDF non è un valido documento UNILAV
        FileNotFoundError: Se il file non esiste
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("Il PDF è vuoto")
            
            # Estrae tutto il testo da tutte le pagine
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n\n"
            
            if not full_text or ("UNILAV" not in full_text.upper() and "Comunicazione Obbligatoria" not in full_text):
                raise ValueError("Il documento non sembra essere un UNILAV valido")
            
            # Parsing dei dati
            datore = _extract_datore_lavoro(full_text)
            lavoratore = _extract_lavoratore(full_text)
            unilav = _extract_unilav_data(full_text)
            
            return {
                "datore": datore,
                "lavoratore": lavoratore,
                "unilav": unilav
            }
            
    except FileNotFoundError:
        raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
    except Exception as e:
        raise ValueError(f"Errore durante il parsing del PDF: {str(e)}")


def _extract_field(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Helper per estrarre un campo con regex"""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if match:
        value = match.group(group).strip()
        return value if value and value != "-" else None
    return None


def _extract_datore_lavoro(text: str) -> DatoreLavoroData:
    """Estrae i dati del datore di lavoro"""
    
    # Codice fiscale datore - supporta entrambi i formati
    # Formato 2021: "codice fiscale: XXXXX"
    # Formato recente: "Codice fiscale: XXXXX"
    cf = _extract_field(text, r'Datore\s+di\s+Lavoro[\s\S]*?codice\s+fiscale:\s*([A-Z0-9]{11,16})')
    if not cf:
        raise ValueError("Codice fiscale datore di lavoro non trovato")
    
    # Denominazione - supporta entrambe le varianti
    # Formato 2021: "denominazione datore lavoro:"
    # Formato recente: "Denominazione datore di lavoro:"
    denominazione = _extract_field(text, r'denominazione\s+datore\s+(?:di\s+)?lavoro:\s*(.+?)(?:\n|$)')
    if not denominazione:
        raise ValueError("Denominazione datore di lavoro non trovata")
    
    # Sede legale
    comune_sede_legale = _extract_field(text, r'comune\s+sede\s+legale:\s*([A-Z\s]+?)(?:\s+CAP)')
    cap_sede_legale = _extract_field(text, r'CAP\s+sede\s+legale:\s*(\d{5})')
    indirizzo_sede_legale = _extract_field(text, r'indirizzo\s+sede\s+legale:\s*(.+?)(?:\n|telefono)')
    
    # Sede di lavoro (se presente)
    comune_sede_lavoro = _extract_field(text, r'comune\s+sede\s+di\s+lavoro:\s*([A-Z\s]+?)(?:\s+CAP)')
    cap_sede_lavoro = _extract_field(text, r'CAP\s+sede\s+di\s+lavoro:\s*(\d{5})')
    indirizzo_sede_lavoro = _extract_field(text, r'indirizzo\s+sede\s+di\s+lavoro:\s*(.+?)(?:\n|telefono)')
    
    # Telefono - prova diversi pattern
    telefono = _extract_field(text, r'telefono:\s*(\d+[\d/\s]*)')
    
    # Email - pattern più flessibile
    email = _extract_field(text, r'(?:e-?mail|indirizzo\s+di\s+posta\s+elettronica):\s*([^\s\n]+@[^\s\n]+)')
    
    return {
        "codice_fiscale": cf,
        "denominazione": denominazione,
        "settore": _extract_field(text, r'settore:\s*(.+?)(?:\n|$)'),
        "comune_sede_legale": comune_sede_legale,
        "cap_sede_legale": cap_sede_legale,
        "indirizzo_sede_legale": indirizzo_sede_legale,
        "telefono": telefono,
        "email": email,
        "comune_sede_lavoro": comune_sede_lavoro,
        "cap_sede_lavoro": cap_sede_lavoro,
        "indirizzo_sede_lavoro": indirizzo_sede_lavoro,
    }


def _extract_lavoratore(text: str) -> LavoratoreData:
    """Estrae i dati del lavoratore"""
    
    # Codice fiscale lavoratore
    cf = _extract_field(text, r'Lavoratore[\s\S]*?codice\s+[Ff]iscale:\s*([A-Z0-9]{16})')
    if not cf:
        raise ValueError("Codice fiscale lavoratore non trovato")
    
    # Cognome e Nome
    cognome = _extract_field(text, r'\bcognome:\s*([A-Z]+)')
    if not cognome:
        raise ValueError("Cognome lavoratore non trovato")
    
    nome = _extract_field(text, r'\bnome:\s*([A-Z]+)')
    if not nome:
        raise ValueError("Nome lavoratore non trovato")
    
    # Sesso
    sesso = _extract_field(text, r'sesso:\s*([MF])')
    
    # Data nascita - converte in formato YYYY-MM-DD
    data_nascita_raw = _extract_field(text, r'data\s+di\s+nascita:\s*(\d{2}/\d{2}/\d{4})')
    data_nascita = None
    if data_nascita_raw:
        try:
            dt = datetime.strptime(data_nascita_raw, "%d/%m/%Y")
            data_nascita = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Comune di nascita
    comune_nascita = _extract_field(text, r'comune\s+(?:o\s+in\s+alternativa\s+stato\s+straniero\s+)?di\s+nascita:\s*([A-Z\s]+?)(?:\n|cittadinanza)')
    
    # Cittadinanza
    cittadinanza = _extract_field(text, r'cittadinanza:\s*([A-Z\s]+?)(?:\s+data\s+di\s+nascita|\n)')
    
    # Domicilio
    comune_domicilio = _extract_field(text, r'comune\s+di\s+domicilio:\s*([A-Z\s]+?)(?:\s+CAP)')
    cap_domicilio = _extract_field(text, r'CAP(?:\s+domicilio)?:\s*(\d{5})')
    indirizzo_domicilio = _extract_field(text, r'indirizzo\s+di\s+domicilio:\s*(.+?)(?:\n|livello)')
    
    # Livello istruzione
    livello_istruzione = _extract_field(text, r'livello\s+di\s+istruzione:\s*(.+?)(?:\n\n|\nInizio|\nDati)')
    
    return {
        "codice_fiscale": cf,
        "cognome": cognome.title(),
        "nome": nome.title(),
        "sesso": sesso,
        "data_nascita": data_nascita,
        "comune_nascita": comune_nascita,
        "cittadinanza": cittadinanza,
        "comune_domicilio": comune_domicilio,
        "cap_domicilio": cap_domicilio,
        "indirizzo_domicilio": indirizzo_domicilio,
        "livello_istruzione": livello_istruzione,
    }


def _extract_unilav_data(text: str) -> UnilavData:
    """Estrae i dati del documento UNILAV"""
    
    codice = _extract_field(text, r'[Cc]odice\s+comunicazione:\s*(\d+)')
    if not codice:
        raise ValueError("Codice comunicazione non trovato")
    
    tipo = _extract_field(text, r'[Tt]ipo\s+comunicazione:\s*(.+?)(?:\n|$)')
    modello = _extract_field(text, r'[Mm]odello:\s*(.+?)(?:\n|$)')
    
    # Centro per l'impiego
    centro_impiego = _extract_field(text, r"[Cc]entro\s+per\s+l['\"]impiego\s+di:\s*([A-Z\s]+?)(?:\n|Provincia)")
    provincia_impiego = _extract_field(text, r'[Pp]rovincia\s+di:\s*([A-Z\s]+?)(?:\n|$)')
    
    # Data comunicazione (trasmissione)
    data_raw = _extract_field(text, r'[Tt]rasmessa\s+il:\s*(\d{2}/\d{2}/\d{4})')
    data_comunicazione = None
    if data_raw:
        try:
            dt = datetime.strptime(data_raw, "%d/%m/%Y")
            data_comunicazione = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Date rapporto
    data_da_raw = _extract_field(text, r'data\s+inizio\s+rapporto:\s*(\d{2}/\d{2}/\d{4})')
    data_da = None
    if data_da_raw:
        try:
            dt = datetime.strptime(data_da_raw, "%d/%m/%Y")
            data_da = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    data_a_raw = _extract_field(text, r'data\s+fine\s+rapporto:\s*(\d{2}/\d{2}/\d{4})')
    data_a = None
    if data_a_raw:
        try:
            dt = datetime.strptime(data_a_raw, "%d/%m/%Y")
            data_a = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Data fine proroga (specifico per comunicazioni di proroga)
    # Approccio ultra-robusto: cerca "fine" + "proroga" e poi la data più vicina
    data_proroga = None
    
    # Pattern 1: "data fine proroga" con o senza due punti, con spazi flessibili
    data_proroga_match = re.search(
        r'data\s+fine\s+proroga\s*:?\s*(\d{2}/\d{2}/\d{4})',
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern 2: Solo "fine proroga" seguito da data
    if not data_proroga_match:
        data_proroga_match = re.search(
            r'fine\s+proroga\s*:?\s*(\d{2}/\d{2}/\d{4})',
            text,
            re.IGNORECASE | re.DOTALL
        )
    
    # Pattern 3: "proroga" seguita da una data nella stessa sezione
    # (esclude date già estratte come data_da e data_a)
    if not data_proroga_match:
        # Cerca nelle sezioni che contengono "Proroga"
        proroga_section = re.search(
            r'(?:Dati\s+)?Proroga.*?(\d{2}/\d{2}/\d{4})',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if proroga_section:
            possible_date = proroga_section.group(1)
            # Verifica che non sia una delle date già estratte
            if possible_date and possible_date not in [data_da_raw, data_a_raw]:
                data_proroga_match = proroga_section
    
    if data_proroga_match:
        data_proroga_raw = data_proroga_match.group(1)
        try:
            dt = datetime.strptime(data_proroga_raw, "%d/%m/%Y")
            data_proroga = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Ente previdenziale e INAIL
    ente_previdenziale = _extract_field(text, r'[Ee]nte\s+[Pp]revidenziale:\s*([A-Z]+)')
    codice_ente = _extract_field(text, r'[Cc]odice\s+[Ee]nte\s+[Pp]revidenziale:\s*(\d+)')
    pat_inail = _extract_field(text, r'PAT\s+INAIL:\s*(\d+)')
    
    # Dati Trasformazione (specifico per comunicazioni di trasformazione)
    data_trasformazione = None
    data_trasf_match = re.search(
        r'data\s+trasformazione\s*:?\s*(\d{2}/\d{2}/\d{4})',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if data_trasf_match:
        data_trasf_raw = data_trasf_match.group(1)
        try:
            dt = datetime.strptime(data_trasf_raw, "%d/%m/%Y")
            data_trasformazione = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Causa trasformazione
    causa_trasformazione = _extract_field(
        text, 
        r'causa\s+trasformazione\s*:?\s*(.+?)(?:\n\n|DETERMINATO|INDETERMINATO|Dati\s+Rapporto|$)'
    )
    
    # Tipologia contrattuale
    tipologia = _extract_field(text, r'[Tt]ipologia\s+contrattuale:\s*(.+?)(?:\n|$)')
    
    # Tipo orario e ore settimanali
    tipo_orario = _extract_field(text, r'[Tt]ipo\s+orario:\s*(.+?)(?:\s+ore\s+settimanali|\n|$)')
    ore_settimanali = _extract_field(text, r'ore\s+settimanali\s+medie:\s*(\d+)')
    
    # Qualifica - gestisce formato con "(ISTAT)" o "(CP 2011)"
    qualifica = _extract_field(text, r'qualifica\s+professionale\s*(?:\([^)]+\))?:\s*(.+?)(?:\n|$)')
    
    # CCNL
    ccnl = _extract_field(text, r'contratto\s+collettivo\s+applicato:\s*(.+?)(?:\n|$)')
    
    # Livello inquadramento
    livello = _extract_field(text, r'livello\s+di\s+inquadramento:\s*(.+?)(?:\n|$)')
    
    # Retribuzione
    retribuzione = _extract_field(text, r'retribuzione\s*/\s*compenso:\s*(\d+)')
    
    # Giornate lavorative
    giornate = _extract_field(text, r'giornate\s+lavorative\s+previste:\s*(\d+)')
    
    # Soggetto comunicazione (se diverso dal datore)
    soggetto = _extract_field(text, r'soggetto\s+che\s+effettua\s+la\s+comunicazione\s*(?:\([^)]+\))?:\s*(.+?)(?:\n|$)')
    cf_soggetto = _extract_field(text, r'[Cc]odice\s+[Ff]iscale\s+del\s+soggetto\s+che\s+effettua\s+la\s+comunicazione\s*(?:\([^)]+\))?:\s*([A-Z0-9]{16})')
    
    return {
        "codice_comunicazione": codice,
        "tipo_comunicazione": tipo or "Comunicazione Obbligatoria",
        "modello": modello,
        "data_comunicazione": data_comunicazione or datetime.now().strftime("%Y-%m-%d"),
        "centro_impiego": centro_impiego,
        "provincia_impiego": provincia_impiego,
        "data_inizio_rapporto": data_da,
        "data_fine_rapporto": data_a,
        "data_proroga": data_proroga,
        "data_trasformazione": data_trasformazione,
        "causa_trasformazione": causa_trasformazione,
        "ente_previdenziale": ente_previdenziale,
        "codice_ente_previdenziale": codice_ente,
        "pat_inail": pat_inail,
        "tipologia_contrattuale": tipologia,
        "tipo_orario": tipo_orario,
        "ore_settimanali": ore_settimanali,
        "qualifica_professionale": qualifica,
        "contratto_collettivo": ccnl,
        "livello_inquadramento": livello,
        "retribuzione": retribuzione,
        "giornate_lavorative": giornate,
        "soggetto_comunicazione": soggetto,
        "cf_soggetto_comunicazione": cf_soggetto,
    }
