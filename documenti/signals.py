"""
Signals per il modulo documenti
"""
import logging
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .models import Documento, AttributoDefinizione, DocumentiTipo
from utils.file_utils import move_to_orphaned

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Documento)
def move_file_on_document_delete(sender, instance, **kwargs):
    """
    Sposta il file in una cartella dedicata "FileNonAssociati" quando viene eliminato un documento.
    Non sovrascrive file esistenti, aggiunge un suffisso numerico progressivo.
    """
    if not instance.file:
        return
    
    try:
        storage = instance.file.storage
        source_path = instance.file.name
        
        destination = move_to_orphaned(storage, source_path)
        
        if destination:
            logger.info(
                f"File spostato in FileNonAssociati dopo cancellazione documento {instance.codice}: "
                f"{source_path} -> {destination}"
            )
        
    except Exception as e:
        logger.error(
            f"Errore nello spostamento del file {instance.file.name} "
            f"per documento {instance.codice}: {str(e)}"
        )


@receiver(pre_save, sender=Documento)
def delete_old_file_on_update(sender, instance, **kwargs):
    """
    Cancella il vecchio file quando viene sostituito con uno nuovo.
    Non cancella se il file viene rimosso esplicitamente (caso gestito dal form).
    """
    if not instance.pk:
        # Nuovo documento, non c'è file vecchio da cancellare
        return

    try:
        old_instance = Documento.objects.get(pk=instance.pk)
    except Documento.DoesNotExist:
        # Il documento non esiste ancora nel DB
        return

    # Se c'era un file vecchio e ora ce n'è uno nuovo diverso
    old_file = old_instance.file
    new_file = instance.file

    if old_file and new_file and old_file.name != new_file.name:
        try:
            if old_file.storage.exists(old_file.name):
                old_file.delete(save=False)
                logger.info(f"File vecchio {old_file.name} eliminato per documento {instance.codice}")
        except Exception as e:
            logger.error(f"Errore nella cancellazione del file vecchio {old_file.name}: {str(e)}")


# ============================================================================
# SIGNALS PER AUTO-AGGIORNAMENTO HELP_DATA
# ============================================================================

@receiver(post_save, sender=AttributoDefinizione)
def auto_rebuild_help_on_attribute_change(sender, instance, **kwargs):
    """
    Quando un AttributoDefinizione viene salvato,
    rigenera automaticamente le sezioni tecniche del help_data.
    """
    from .help_builder import rebuild_help_technical_sections
    
    tipo_documento = instance.tipo_documento
    
    if tipo_documento and tipo_documento.help_data:
        # Rigenera solo se help_data esiste già
        try:
            tipo_documento.help_data = rebuild_help_technical_sections(tipo_documento)
            tipo_documento.save(update_fields=['help_data'])
            logger.info(
                f"Help_data rigenerato automaticamente per {tipo_documento.codice} "
                f"dopo modifica attributo {instance.codice}"
            )
        except Exception as e:
            logger.error(
                f"Errore nella rigenerazione help_data per {tipo_documento.codice}: {e}"
            )


@receiver(post_delete, sender=AttributoDefinizione)
def auto_rebuild_help_on_attribute_delete(sender, instance, **kwargs):
    """
    Quando un AttributoDefinizione viene eliminato,
    rigenera automaticamente le sezioni tecniche del help_data.
    """
    from .help_builder import rebuild_help_technical_sections
    
    tipo_documento = instance.tipo_documento
    
    if tipo_documento and tipo_documento.help_data:
        try:
            tipo_documento.help_data = rebuild_help_technical_sections(tipo_documento)
            tipo_documento.save(update_fields=['help_data'])
            logger.info(
                f"Help_data rigenerato automaticamente per {tipo_documento.codice} "
                f"dopo eliminazione attributo {instance.codice}"
            )
        except Exception as e:
            logger.error(
                f"Errore nella rigenerazione help_data per {tipo_documento.codice}: {e}"
            )


@receiver(post_save, sender=DocumentiTipo)
def auto_initialize_help_data(sender, instance, created, **kwargs):
    """
    Quando un nuovo DocumentiTipo viene creato,
    inizializza automaticamente le sezioni tecniche del help_data.
    """
    if created and not instance.help_data:
        from .help_builder import HelpDataBuilder
        
        try:
            builder = HelpDataBuilder(instance)
            
            # Inizializza solo sezioni tecniche + placeholders per le discorsive
            instance.help_data = builder.build_all_technical_sections()
            
            # Aggiungi placeholder per sezioni discorsive
            instance.help_data.update({
                'descrizione_breve': f'Tipo documento {instance.nome}',
                'quando_usare': {
                    'casi_uso': [],
                    'non_usare_per': [],
                },
                'workflow': {
                    'stati_possibili': ['Bozza', 'Protocollato', 'Archiviato'],
                    'stato_iniziale': 'Bozza',
                    'azioni_disponibili': [],
                },
                'note_speciali': {
                    'attenzioni': [],
                    'suggerimenti': [],
                    'vincoli_business': [],
                },
                'faq': [],
                'risorse_correlate': {
                    'guide_correlate': [],
                    'tipi_documento_correlati': [],
                },
            })
            
            instance.save(update_fields=['help_data'])
            logger.info(
                f"Help_data inizializzato automaticamente per nuovo tipo {instance.codice}"
            )
        except Exception as e:
            logger.error(
                f"Errore nell'inizializzazione help_data per {instance.codice}: {e}"
            )
