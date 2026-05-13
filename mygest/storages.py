from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os


def _is_r2_configured():
    r2 = getattr(settings, 'CLOUDFLARE_R2', {})
    return bool(r2.get('BUCKET_NAME') and r2.get('ACCOUNT_ID'))


def _build_r2_backend():
    from storages.backends.s3boto3 import S3Boto3Storage
    r2 = settings.CLOUDFLARE_R2
    return S3Boto3Storage(
        bucket_name=r2['BUCKET_NAME'],
        endpoint_url=f"https://{r2['ACCOUNT_ID']}.r2.cloudflarestorage.com",
        access_key=r2['ACCESS_KEY_ID'],
        secret_key=r2['SECRET_ACCESS_KEY'],
        region_name='auto',
        default_acl=None,
        # URL firmati con scadenza: il bucket rimane privato,
        # ogni URL contiene una firma temporanea generata da Django.
        querystring_auth=True,
        querystring_expire=r2.get('URL_EXPIRY_SECONDS', 3600),
        file_overwrite=False,
    )


class NASPathStorage(FileSystemStorage):
    """
    Smart storage: usa Cloudflare R2 quando configurato (produzione),
    filesystem locale altrimenti (sviluppo/test).
    """

    def __init__(self, location=None, base_url=None):
        super().__init__(
            location=location or settings.ARCHIVIO_BASE_PATH,
            base_url=base_url or settings.MEDIA_URL,
        )
        self._r2 = _build_r2_backend() if _is_r2_configured() else None

    @property
    def location(self):
        return settings.ARCHIVIO_BASE_PATH

    def path(self, name):
        if self._r2:
            raise NotImplementedError("path() non supportato con Cloudflare R2")
        name = str(name).replace("\\", "/")
        return os.path.join(self.location, name)

    def _open(self, name, mode='rb'):
        return self._r2._open(name, mode) if self._r2 else super()._open(name, mode)

    def _save(self, name, content):
        return self._r2._save(name, content) if self._r2 else super()._save(name, content)

    def delete(self, name):
        return self._r2.delete(name) if self._r2 else super().delete(name)

    def exists(self, name):
        return self._r2.exists(name) if self._r2 else super().exists(name)

    def size(self, name):
        return self._r2.size(name) if self._r2 else super().size(name)

    def url(self, name):
        return self._r2.url(name) if self._r2 else super().url(name)

    def get_available_name(self, name, max_length=None):
        if self._r2:
            return self._r2.get_available_name(name, max_length)
        return super().get_available_name(name, max_length)
