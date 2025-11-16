from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class NASPathStorage(FileSystemStorage):
    """
    Storage che usa SEMPRE la root corrente da settings.ARCHIVIO_BASE_PATH.
    Evita di “congelare” la location a import-time, così i test che patchano
    settings funzionano (startswith(nas_tmp)).
    """
    def __init__(self, location=None, base_url=None):
        super().__init__(
            location=location or settings.ARCHIVIO_BASE_PATH,
            base_url=base_url or settings.MEDIA_URL,
        )

    @property
    def location(self):
        # Qualsiasi metodo di FileSystemStorage che usa self.location
        # leggerà il valore aggiornato dai settings.
        return settings.ARCHIVIO_BASE_PATH

    def path(self, name):
        # Garantiamo che il path assoluto usi la location corrente.
        name = str(name).replace("\\", "/")
        return os.path.join(self.location, name)
