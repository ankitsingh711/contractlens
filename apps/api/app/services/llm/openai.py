from openai import AsyncOpenAI

from app.services.llm.base import LLMMessage, LLMProvider, LLMResponse


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(
        self, messages: list[LLMMessage], *, temperature: float = 0.0
    ) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
