"""
Servizio per importazione ClassificationResult → Documento
"""
import logging
import shutil
from pathlib import Path
from typing import List
from django.db import transaction
from django.core.files import File

from documenti.models import Documento, DocumentiTipo
from titolario.models import TitolarioVoce
from ..models import ClassificationResult

logger = logging.getLogger(__name__)


class DocumentImporter:
    """
    Importa ClassificationResult come Documento nell'app documenti.
    Gestisce copia file, creazione record, e aggiornamento stato.
    """
    
    # Mapping tipo classificazione → DocumentiTipo codice
    TYPE_MAPPING = {
        'CED': 'CED',  # Cedolino
        'UNI': 'UNI',  # Unilav
        'DIC': 'DIC',  # Dichiarazione
        'BIL': 'BIL',  # Bilancio
        'F24': 'F24',  # F24
        'EST': 'EST',  # Estratto Conto
        'FAT': 'FAT',  # Fattura
        'CON': 'CON',  # Contratto
        'COR': 'COR',  # Corrispondenza
        'PRO': 'PRO',  # Protocollo
        'ALT': 'ALT',  # Altro
    }
    
    def __init__(self, copy_files: bool = True, delete_source: bool = False):
        """
        Inizializza l'importer.
        
        Args:
            copy_files: Se True, copia file nel NAS
            delete_source: Se True, elimina file sorgente dopo import
        """
        self.copy_files = copy_files
        self.delete_source = delete_source
    
    @transaction.atomic
    def import_results(
        self,
        result_ids: List[int],
        user
    ) -> List[Documento]:
        """
        Importa una lista di ClassificationResult come Documenti.
        
        Args:
            result_ids: Lista di ID ClassificationResult
            user: User che esegue l'import
            
        Returns:
            Lista di Documento creati
        """
        results = ClassificationResult.objects.filter(
            id__in=result_ids,
            imported=False
        ).select_related('suggested_cliente', 'suggested_fascicolo', 'suggested_titolario')
        
        if not results.exists():
            raise ValueError("Nessun risultato valido da importare")
        
        documenti_creati = []
        
        for result in results:
            try:
                documento = self._import_single_result(result, user)
                documenti_creati.append(documento)
                logger.info(f"Importato {result.file_name} → Documento {documento.codice}")
            except Exception as e:
                logger.error(f"Errore import {result.file_name}: {e}", exc_info=True)
                # Continua con i prossimi (non blocca tutto il batch)
                continue
        
        return documenti_creati
    
    def _import_single_result(self, result: ClassificationResult, user) -> Documento:
        """Importa un singolo ClassificationResult come Documento"""
        
        # Step 1: Determina tipo documento
        tipo_codice = self.TYPE_MAPPING.get(result.predicted_type, 'ALT')
        tipo_documento = self._get_or_create_tipo_documento(tipo_codice)
        
        # Step 2: Determina cliente
        cliente = result.suggested_cliente
        if not cliente and result.suggested_fascicolo:
            cliente = result.suggested_fascicolo.cliente
        
        # Step 3: Determina titolario
        titolario = result.suggested_titolario
        if not titolario:
            # Usa titolario di default o prova a inferirlo dal tipo
            titolario = self._get_default_titolario_for_type(result.predicted_type)
        
        # Step 4: Prepara metadata documento
        metadata = result.extracted_metadata or {}
        
        # Estrai data documento da metadata
        data_documento = metadata.get('data_documento')
        if data_documento:
            # Converti da ISO string a date
            from datetime import datetime
            data_documento = datetime.fromisoformat(data_documento).date()
        
        # Step 5: Crea documento
        documento = Documento(
            tipo=tipo_documento,
            cliente=cliente,
            fascicolo=result.suggested_fascicolo,
            titolario_voce=titolario,
            descrizione=self._generate_title(result),
            digitale=True,  # File da filesystem sono considerati digitali
            tracciabile=True,
            data_documento=data_documento,
            note=f"Importato da AI Classifier\n"
                 f"Metodo: {result.classification_method}\n"
                 f"Confidenza: {result.confidence_score:.2%}\n"
                 f"{result.notes}".strip(),
        )
        
        # Step 6: Gestisci file
        if self.copy_files and Path(result.file_path).exists():
            # Apri file e assegna a documento.file
            with open(result.file_path, 'rb') as f:
                django_file = File(f, name=result.file_name)
                documento.file.save(result.file_name, django_file, save=False)
        
        # Salva documento (trigger save() che gestisce percorso_archivio, codice, etc.)
        documento.save()
        
        # Step 7: Elimina file sorgente se richiesto
        if self.delete_source and Path(result.file_path).exists():
            try:
                Path(result.file_path).unlink()
                logger.info(f"File sorgente eliminato: {result.file_path}")
            except Exception as e:
                logger.warning(f"Impossibile eliminare file sorgente {result.file_path}: {e}")
        
        # Step 8: Aggiorna ClassificationResult
        result.mark_as_imported(documento)
        
        return documento
    
    def _get_or_create_tipo_documento(self, codice: str) -> DocumentiTipo:
        """Ottiene o crea DocumentiTipo"""
        tipo, created = DocumentiTipo.objects.get_or_create(
            codice=codice,
            defaults={
                'nome': self._get_tipo_nome(codice),
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}'
            }
        )
        if created:
            logger.info(f"Creato DocumentiTipo: {codice}")
        return tipo
    
    def _get_tipo_nome(self, codice: str) -> str:
        """Ritorna nome user-friendly per tipo documento"""
        nomi = {
            'CED': 'Cedolino',
            'UNI': 'Unilav',
            'DIC': 'Dichiarazione Fiscale',
            'BIL': 'Bilancio',
            'F24': 'F24',
            'EST': 'Estratto Conto',
            'FAT': 'Fattura',
            'CON': 'Contratto',
            'COR': 'Corrispondenza',
            'PRO': 'Protocollo',
            'ALT': 'Altro',
        }
        return nomi.get(codice, 'Documento')
    
    def _get_default_titolario_for_type(self, doc_type: str) -> TitolarioVoce:
        """Ritorna voce titolario di default per tipo documento"""
        # Mapping tipo → codice titolario (da adattare ai tuoi codici titolario)
        titolario_mapping = {
            'CED': '04.03',  # Cedolini (esempio)
            'UNI': '04.02',  # Comunicazioni obbligatorie
            'DIC': '03.02',  # Dichiarazioni fiscali
            'BIL': '03.01',  # Bilanci
            'F24': '03.03',  # Tributi
            'EST': '02.05',  # Estratti conto
            'FAT': '01.02',  # Fatture
        }
        
        codice_titolario = titolario_mapping.get(doc_type)
        
        if codice_titolario:
            try:
                return TitolarioVoce.objects.get(codice=codice_titolario)
            except TitolarioVoce.DoesNotExist:
                pass
        
        # Fallback a "99 - Varie"
        from documenti.models import get_or_create_default_titolario
        return get_or_create_default_titolario()
    
    def _generate_title(self, result: ClassificationResult) -> str:
        """Genera titolo documento da metadata"""
        metadata = result.extracted_metadata or {}
        
        # Prova a costruire titolo da metadata
        parts = []
        
        # Tipo documento
        parts.append(result.get_predicted_type_display())
        
        # Periodo/Anno
        if 'periodo_riferimento' in metadata:
            parts.append(metadata['periodo_riferimento'])
        elif 'anno' in metadata:
            parts.append(str(metadata['anno']))
        
        # Numero documento
        if 'numero_documento' in metadata:
            parts.append(f"n. {metadata['numero_documento']}")
        
        # Se nessun metadata utile, usa filename
        if len(parts) == 1:
            # Rimuovi estensione da filename
            filename_no_ext = Path(result.file_name).stem
            return filename_no_ext
        
        return " - ".join(parts)
