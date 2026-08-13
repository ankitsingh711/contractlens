import re

from app.services.llm.base import LLMMessage, LLMProvider, LLMResponse

_EVIDENCE_BLOCK_RE = re.compile(r"\[(\d+)\][^\n]*:\s*(.*?)(?=\n\n\[\d+\]|\Z)", re.DOTALL)


def _first_sentence(text: str, max_chars: int = 280) -> str:
    text = " ".join(text.split())
    match = re.search(r"^.{0,%d}?[.;]" % max_chars, text)
    sentence = match.group(0) if match else text[:max_chars]
    return sentence.strip()


class MockLLMProvider(LLMProvider):
    """Deterministic, dependency-free chat completion for demo mode.

    Does not call any external API. It extracts the top cited evidence
    block from the prompt (produced by the RAG service, formatted as
    `[n] (Section ..., Page ...): <chunk text>`) and answers using only
    that text, always citing it — this lets the citation-validation logic
    downstream be exercised end-to-end without a real model.
    """

    def __init__(self, model: str = "mock-llm"):
        self.model = model

    async def complete(
        self, messages: list[LLMMessage], *, temperature: float = 0.0
    ) -> LLMResponse:
        user_content = next((m.content for m in messages if m.role == "user"), "")
        blocks = _EVIDENCE_BLOCK_RE.findall(user_content)

        if not blocks:
            text = "I couldn't determine this from the provided documents."
        else:
            index, evidence_text = blocks[0]
            sentence = _first_sentence(evidence_text)
            text = f"Based on the available evidence, {sentence} [{index}]"

        input_tokens = len(user_content.split())
        output_tokens = len(text.split())
        return LLMResponse(
            text=text, model=self.model, input_tokens=input_tokens, output_tokens=output_tokens
        )
