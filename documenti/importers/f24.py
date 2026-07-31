"""
Importatore per Modelli F24.
Integrato con parser esistente documenti/parsers/f24_parser.py
"""

import os
import zipfile
import tempfile
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from django.db import transaction
from django.utils import timezone
from django.core.files import File

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from .base import BaseImporter, ParseResult, ImporterRegistry
from ..parsers.f24_parser import parse_f24_pdf
from ..models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore, get_or_create_default_titolario
from anagrafiche.models import Cliente
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


def _build_descrizione(
    denominazione: Optional[str],
    codice_fiscale: str,
    data_scadenza: Optional[str],
    importo_saldo: Optional[str],
) -> str:
    """Descrizione documento F24, con totale della delega come elemento informativo."""
    parti = [f"F24 {denominazione or codice_fiscale}"]
    parti.append(f"Scad. {data_scadenza}" if data_scadenza else "Scad. n.d.")
    if importo_saldo:
        parti.append(f"Tot. € {importo_saldo}")
    return " - ".join(parti)


@ImporterRegistry.register
class F24Importer(BaseImporter):
    """
    Importatore per Modelli F24.

    Supporta:
    - File PDF singolo
    - File ZIP con multipli PDF
    - Estrazione: codice fiscale contribuente, data scadenza rata
    - Match automatico cliente da CF (nessuna creazione automatica:
      il contribuente di un F24 deve già essere un cliente esistente)
    """

    tipo = 'f24'
    display_name = 'Modelli F24'
    supported_extensions = ['.pdf', '.zip']
    max_file_size_mb = 100
    batch_mode = True

    def extract_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Estrae PDF da ZIP o ritorna singolo PDF.
        """
        documents = []

        if file_path.lower().endswith('.zip'):
            temp_dir = tempfile.mkdtemp(prefix='f24_import_')
            self.session.temp_dir = temp_dir
            self.session.save()

            logger.info(f"Estrazione ZIP F24 in {temp_dir}")

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if zip_ref.testzip():
                    raise ValueError("File ZIP corrotto")

                ordine = 0
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue
                    if not file_info.filename.lower().endswith('.pdf'):
                        continue

                    extracted_path = zip_ref.extract(file_info, temp_dir)
                    documents.append({
                        'filename': os.path.basename(file_info.filename),
                        'file_path': extracted_path,
                        'file_size': os.path.getsize(extracted_path),
                        'ordine': ordine,
                    })
                    ordine += 1

            if not documents:
                raise ValueError("Nessun PDF trovato nello ZIP")
        else:
            documents.append({
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'ordine': 0,
            })

        return documents

    def parse_document(self, file_path: str, filename: str) -> ParseResult:
        """
        Parserizza Modello F24 PDF usando parser esistente.
        """
        try:
            logger.info(f"Parsing F24: {filename}")

            parsed = parse_f24_pdf(file_path)

            codice_fiscale = parsed['codice_fiscale']
            data_scadenza = parsed['data_scadenza']  # None se il modulo non riporta una scadenza
            denominazione = parsed.get('denominazione')
            importo_saldo = parsed.get('importo_saldo')

            anagrafiche = []
            match = self.match_anagrafica(codice_fiscale)
            if match:
                match['ruolo'] = 'contribuente'
                match['denominazione'] = denominazione or match.get('nome')
                anagrafiche.append(match)
            else:
                anagrafiche.append({
                    'codice_fiscale': codice_fiscale,
                    'nome': denominazione or codice_fiscale,
                    'match_type': 'not_found',
                    'ruolo': 'contribuente',
                    'denominazione': denominazione,
                })

            valori_editabili = {
                'codice_fiscale': codice_fiscale,
                'data_scadenza': data_scadenza,
                'denominazione': denominazione,
                'importo_saldo': importo_saldo,
            }

            descrizione = _build_descrizione(denominazione, codice_fiscale, data_scadenza, importo_saldo)

            mappatura_db = {
                'tipo': 'Modello',
                'tipo_documento_codice': 'F24',
                'descrizione': descrizione,
                'data_documento': data_scadenza,
                'digitale': True,
                'tracciabile': True,
                'attributi': [
                    {'codice': 'data_scadenza', 'nome': 'Data Scadenza', 'valore': data_scadenza},
                    {'codice': 'Tipo', 'nome': 'Tipo', 'valore': 'Modello'},
                    {'codice': 'Tipo_pagamento', 'nome': 'Tipo pagamento', 'valore': None},
                    {'codice': 'codice_fiscale', 'nome': 'Codice Fiscale Contribuente', 'valore': codice_fiscale},
                ],
                'note_preview': (
                    f"Codice Fiscale/P.IVA: {codice_fiscale}\n"
                    f"Data Scadenza: {data_scadenza or 'non presente nel modulo'}"
                    + (f"\nContribuente: {denominazione}" if denominazione else "")
                    + (f"\nTotale delega: € {importo_saldo}" if importo_saldo else "")
                ),
            }

            return ParseResult(
                success=True,
                parsed_data=parsed,
                anagrafiche_reperite=anagrafiche,
                valori_editabili=valori_editabili,
                mappatura_db=mappatura_db,
            )

        except Exception as e:
            import traceback
            logger.error(f"Errore parsing F24 {filename}: {e}")
            logger.error(traceback.format_exc())

            return ParseResult(
                success=False,
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={},
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )

    def check_duplicate(
        self,
        parsed_data: Dict[str, Any],
        valori_editabili: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica se l'F24 è un duplicato senza crearlo.
        """
        from documenti.services.duplicate_detection import DuplicateDetectionService

        tipo_f24 = DocumentiTipo.objects.filter(codice='F24').first()
        if not tipo_f24:
            return {'is_duplicate': False, 'duplicate_info': None}

        valori = valori_editabili or {}
        cf = valori.get('codice_fiscale') or parsed_data.get('codice_fiscale')

        cliente = None
        if cf:
            cliente = Cliente.objects.filter(
                anagrafica__codice_fiscale__iexact=cf
            ).select_related('anagrafica').first()

        if not cliente:
            return {'is_duplicate': False, 'duplicate_info': None}

        attributi_per_verifica = {
            'data_scadenza': valori.get('data_scadenza') or parsed_data.get('data_scadenza'),
        }

        service = DuplicateDetectionService(tipo_f24)

        if not service.is_enabled():
            return {'is_duplicate': False, 'duplicate_info': None}

        result = service.find_duplicate(
            cliente=cliente,
            attributi=attributi_per_verifica,
            documento_fields={'data_documento': timezone.now().date()}
        )

        if result.is_duplicate:
            return {
                'is_duplicate': True,
                'duplicate_info': {
                    'id': result.documento.id,
                    'codice': result.documento.codice,
                    'data_scadenza': attributi_per_verifica.get('data_scadenza'),
                    'confidence': result.confidence,
                    'matched_fields': result.matched_fields,
                }
            }

        return {'is_duplicate': False, 'duplicate_info': None}

    @transaction.atomic
    def create_documento(
        self,
        parsed_data: Dict[str, Any],
        valori_editati: Dict[str, Any],
        user: 'User',
        **kwargs
    ) -> 'Documento':
        """
        Crea documento F24 nel DB dai dati parsati + valori editati dall'utente.

        Il cliente deve già esistere: se il CF non matcha nessun cliente e non
        viene fornito esplicitamente `cliente_id`, viene sollevato ValueError
        per richiedere la selezione manuale nel wizard di importazione.
        """
        logger.info(f"Creazione documento F24 per utente {user.username}")

        codice_fiscale = valori_editati['codice_fiscale']
        data_scadenza_str = valori_editati.get('data_scadenza')  # None se assente nel modulo

        from datetime import datetime
        if isinstance(data_scadenza_str, str):
            data_scadenza = datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
        elif data_scadenza_str is None:
            data_scadenza = None
        else:
            data_scadenza = data_scadenza_str

        # 1. Risoluzione cliente (nessuna auto-creazione)
        cliente_id = kwargs.get('cliente_id')
        if cliente_id:
            cliente = Cliente.objects.get(id=cliente_id)
        else:
            cliente = Cliente.objects.filter(
                anagrafica__codice_fiscale__iexact=codice_fiscale
            ).select_related('anagrafica').first()

        if not cliente:
            raise ValueError(
                f"Cliente non trovato per CF {codice_fiscale}: selezionare manualmente il cliente"
            )

        # 2. Recupera/Crea Tipo F24
        tipo_f24, _ = DocumentiTipo.objects.get_or_create(
            codice='F24',
            defaults={'nome': 'Modello di versamento F24', 'estensioni_permesse': 'pdf'}
        )

        # 3. Titolario: usa la voce F24 esistente sotto AF/AF-TAX (Imposte e tasse),
        # con fallback alla voce di default se non configurata nell'ambiente
        titolario_voce = (
            TitolarioVoce.objects.filter(codice='F24', parent__codice='AF-TAX').first()
            or get_or_create_default_titolario()
        )

        # 4. Crea Documento
        denominazione = valori_editati.get('denominazione')
        importo_saldo = valori_editati.get('importo_saldo')
        descrizione = _build_descrizione(denominazione, codice_fiscale, data_scadenza_str, importo_saldo)

        documento = Documento.objects.create(
            tipo=tipo_f24,
            cliente=cliente,
            titolario_voce=titolario_voce,
            descrizione=descrizione,
            # Se il modulo non riporta una scadenza, usa la data odierna
            # (Documento.data_documento non è nullable)
            data_documento=data_scadenza or timezone.now().date(),
            digitale=True,
            tracciabile=True,
            stato=Documento.Stato.DEFINITIVO,
        )

        logger.info(f"Creato documento F24 #{documento.id}: {descrizione}")

        # 5. Salva Attributi Dinamici PRIMA di allegare il file
        attributi_map = {
            'data_scadenza': data_scadenza_str,
            'Tipo': 'Modello',
            'Tipo_pagamento': None,
        }

        attrs_map_for_rename = {}

        for codice_attr, valore in attributi_map.items():
            try:
                definizione = AttributoDefinizione.objects.get(
                    tipo_documento=tipo_f24,
                    codice=codice_attr
                )

                AttributoValore.objects.update_or_create(
                    documento=documento,
                    definizione=definizione,
                    defaults={'valore': valore}
                )

                attrs_map_for_rename[codice_attr] = valore

                logger.debug(f"Salvato attributo '{codice_attr}': {valore}")

            except AttributoDefinizione.DoesNotExist:
                logger.warning(f"Attributo '{codice_attr}' non configurato per F24, saltato")

        # 6. Allega file PDF DOPO aver salvato gli attributi
        file_path = kwargs.get('file_path')
        if file_path and os.path.exists(file_path):
            documento._skip_auto_rename = True

            with open(file_path, 'rb') as f:
                documento.file.save(
                    os.path.basename(file_path),
                    File(f),
                    save=True
                )

            documento.applica_rename_con_attributi(attrs=attrs_map_for_rename)

        logger.info(f"✓ Documento F24 #{documento.id} creato con successo")

        return documento
