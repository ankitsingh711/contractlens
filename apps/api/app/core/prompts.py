from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


@lru_cache
def load_prompt(task: str, version: str = "v1") -> str:
    """Loads a versioned prompt template from the repo-root `prompts/`
    directory (see docs/evaluation.md for why prompts are files, not
    inline strings: every agent run records the exact version used)."""
    path = Path(get_settings().PROMPTS_DIR) / task / f"{version}.txt"
    return path.read_text()
