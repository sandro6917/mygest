"""
Plugin system per importatori di documenti.

Ogni importer deve estendere BaseImporter e registrarsi con @ImporterRegistry.register
"""

from .base import BaseImporter, ParseResult, ImporterRegistry

# Importatori registrati (auto-register tramite decorator)
from .cedolini import CedoliniImporter
from .unilav import UNILAVImporter

__all__ = [
    'BaseImporter',
    'ParseResult',
    'ImporterRegistry',
    'CedoliniImporter',
    'UNILAVImporter',
]

# Verifica importatori registrati
import logging
logger = logging.getLogger(__name__)
logger.info(f"Importatori registrati: {', '.join(ImporterRegistry._importers.keys())}")

