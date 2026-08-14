import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

DEFAULT_DATASET_VERSION = "qa_eval_v1"


@dataclass
class EvalCase:
    id: str
    document_filename: str
    category: str
    question: str
    expected_answer: str | None
    expected_sources: list[str]

    @property
    def should_abstain(self) -> bool:
        return len(self.expected_sources) == 0


@dataclass
class EvalDataset:
    version: str
    description: str
    cases: list[EvalCase]


@lru_cache
def load_dataset(version: str = DEFAULT_DATASET_VERSION) -> EvalDataset:
    path = Path(get_settings().EVALUATION_DATASET_DIR) / f"{version}.json"
    raw = json.loads(path.read_text())
    cases = [
        EvalCase(
            id=c["id"],
            document_filename=c["document_filename"],
            category=c["category"],
            question=c["question"],
            expected_answer=c.get("expected_answer"),
            expected_sources=c.get("expected_sources", []),
        )
        for c in raw["cases"]
    ]
    return EvalDataset(version=version, description=raw["description"], cases=cases)
