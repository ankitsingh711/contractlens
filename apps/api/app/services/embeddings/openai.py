from openai import AsyncOpenAI

from app.services.embeddings.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dimensions: int):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._model, input=texts, dimensions=self.dimensions
        )
        return [item.embedding for item in response.data]
