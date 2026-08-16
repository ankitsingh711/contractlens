from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorageBackend
from app.services.storage.s3 import S3StorageBackend

__all__ = ["StorageBackend", "get_storage_backend"]


@lru_cache
def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return LocalStorageBackend(root=settings.STORAGE_LOCAL_PATH)
