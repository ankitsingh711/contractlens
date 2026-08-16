from pathlib import Path

import aiofiles

from app.services.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Stores objects on local disk. Used for local development only —
    production deployments use S3StorageBackend behind the same interface."""

    def __init__(self, root: str, public_base_url: str = "/storage"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.public_base_url = public_base_url

    def _path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key.")
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

    async def get(self, key: str) -> bytes:
        path = self._path_for(key)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> None:
        path = self._path_for(key)
        path.unlink(missing_ok=True)

    async def url_for(self, key: str, expires_in: int = 3600) -> str:
        return f"{self.public_base_url}/{key}"
