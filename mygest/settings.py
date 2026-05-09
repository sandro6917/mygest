"""
Django settings wrapper per MyGest.

Questo file importa la configurazione modulare da mygest/settings/
basata sull'ambiente (development o production).

Per modificare le impostazioni, edita:
- mygest/settings/base.py       (configurazione comune)
- mygest/settings/development.py (solo development)
- mygest/settings/production.py  (solo production)

NON modificare questo file direttamente.

DEPRECATION NOTICE:
Il vecchio settings.py monolitico è stato rinominato in settings_old.py
e sarà rimosso in versione 2.0. Usa la struttura modulare.
"""

# Import all settings from modular structure
from mygest.settings import *  # noqa: F401, F403

# Export DEBUG for external checks (es. middleware, templates)
__all__ = ['DEBUG']
