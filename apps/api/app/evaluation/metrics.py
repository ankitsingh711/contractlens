import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_CITATION_MARKER_RE = re.compile(r"\[\d+\]")


def lexical_overlap(a: str, b: str) -> float:
    """Jaccard similarity over lowercased tokens — a crude but honest
    proxy for answer relevance/correctness when the LLM provider may be
    the deterministic mock (see docs/evaluation.md for why a real
    LLM-as-judge is future work, not implemented here)."""
    tokens_a = set(_TOKEN_RE.findall(a.lower()))
    tokens_b = set(_TOKEN_RE.findall(b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


_LEADING_MARKERS_RE = re.compile(r"^((?:\[\d+\]\s*)+)(.*)$")


def faithfulness_score(answer: str) -> float:
    """Fraction of sentences in the answer that carry a citation marker —
    the same heuristic the agent's validate_claims node uses, applied
    here as a numeric score rather than a pass/fail warning.

    Citation markers are conventionally written *after* the sentence they
    support ("claim. [1]"), which means a naive split on ". " leaves the
    marker glued to the front of the *next* fragment. This re-attaches
    any such leading marker(s) to the sentence that just ended before
    scoring, so "claim. [1]" is correctly counted as cited.
    """
    raw_parts = [p.strip() for p in _SENTENCE_RE.split(answer) if p.strip()]
    sentences: list[str] = []
    for part in raw_parts:
        match = _LEADING_MARKERS_RE.match(part)
        if match and sentences:
            markers, remainder = match.group(1).strip(), match.group(2).strip()
            sentences[-1] = f"{sentences[-1]} {markers}"
            if remainder:
                sentences.append(remainder)
        else:
            sentences.append(part)

    if not sentences:
        return 0.0
    cited = sum(1 for s in sentences if _CITATION_MARKER_RE.search(s))
    return cited / len(sentences)


@dataclass
class CaseMetrics:
    retrieval_recall: float
    retrieval_precision: float
    citation_accuracy: float
    faithfulness: float
    answer_relevance: float
    hallucinated: bool
    passed: bool


def compute_case_metrics(
    *,
    should_abstain: bool,
    abstained: bool,
    retrieved_sections: set[str],
    expected_sections: set[str],
    citation_sections: set[str],
    answer: str | None,
    expected_answer: str | None,
) -> CaseMetrics:
    if expected_sections:
        overlap = len(retrieved_sections & expected_sections)
        retrieval_recall = overlap / len(expected_sections)
        retrieval_precision = overlap / len(retrieved_sections) if retrieved_sections else 0.0
    else:
        # Abstention cases have no "correct" section to retrieve — scored
        # as trivially satisfied rather than penalizing the small share
        # of the dataset that's deliberately unanswerable. See
        # docs/evaluation.md for this simplification's trade-off.
        retrieval_recall = 1.0
        retrieval_precision = 1.0

    if citation_sections:
        citation_accuracy = len(citation_sections & expected_sections) / len(citation_sections)
    else:
        citation_accuracy = 1.0 if (should_abstain and abstained) else 0.0

    faithfulness = faithfulness_score(answer) if (answer and not abstained) else (1.0 if abstained else 0.0)

    if should_abstain:
        answer_relevance = 1.0 if abstained else 0.0
    elif abstained:
        answer_relevance = 0.0
    else:
        answer_relevance = lexical_overlap(answer or "", expected_answer or "")

    hallucinated = (not abstained) and (should_abstain or citation_accuracy == 0.0)

    if should_abstain:
        passed = abstained
    else:
        passed = (not abstained) and citation_accuracy > 0.0

    return CaseMetrics(
        retrieval_recall=retrieval_recall,
        retrieval_precision=retrieval_precision,
        citation_accuracy=citation_accuracy,
        faithfulness=faithfulness,
        answer_relevance=answer_relevance,
        hallucinated=hallucinated,
        passed=passed,
    )
