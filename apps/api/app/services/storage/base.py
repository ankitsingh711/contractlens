from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstraction over object storage so the rest of the app never depends
    on whether files live on local disk (dev) or S3 (production)."""

    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def get(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def url_for(self, key: str, expires_in: int = 3600) -> str:
        """Return a URL the client can use to fetch the object directly."""
        ...
