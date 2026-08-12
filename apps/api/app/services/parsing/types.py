from dataclasses import dataclass


@dataclass
class ParsedPage:
    number: int | None
    text: str
