"""
Plugin system per importatori di documenti.

Ogni importer deve estendere BaseImporter e registrarsi con @ImporterRegistry.register
"""

from .base import BaseImporter, ParseResult, ImporterRegistry

# Importatori registrati (auto-register tramite decorator)
from .cedolini import CedoliniImporter
from .certificazioni_uniche import CertificazioniUnicheImporter
from .unilav import UNILAVImporter
from .f24 import F24Importer

__all__ = [
    'BaseImporter',
    'ParseResult',
    'ImporterRegistry',
    'CedoliniImporter',
    'CertificazioniUnicheImporter',
    'UNILAVImporter',
    'F24Importer',
]

# Verifica importatori registrati
import logging
logger = logging.getLogger(__name__)
logger.info(f"Importatori registrati: {', '.join(ImporterRegistry._importers.keys())}")

