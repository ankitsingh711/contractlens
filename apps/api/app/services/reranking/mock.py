import re

from app.services.reranking.base import RerankCandidate, Reranker, RerankResult

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Common English + contract-boilerplate words filtered out before scoring
# overlap. Without this, a query sharing only stopwords and generic
# contract vocabulary ("agreement", "party", "shall") with a chunk can
# clear a low evidence threshold purely on connector-word noise, even
# when the query is about something the document never mentions.
_STOPWORDS = frozenset(
    """
    a an the this that these those is are was were be been being
    of for to in on at by with under over from into onto
    and or but if then than as
    what which who whom whose when where why how
    do does did will would shall should can could may might must
    it its it's he she they them their his her our your my
    not no nor
    agreement party parties hereby herein thereof pursuant
    described
    """.split()
)
# "described" is filtered alongside "agreement"/"party"/"shall" above: it is
# a generic cross-reference verb ("the Services described in each SOW", "as
# described herein") that shows up in almost every contract regardless of
# subject matter, so on its own it is not evidence a query's real subject
# was found in a document.


def _significant_tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


class MockReranker(Reranker):
    """Deterministic, dependency-free reranker for demo mode.

    Scores each candidate by what fraction of the query's distinct,
    non-stopword terms it contains (a simple lexical-overlap heuristic),
    not a cross-encoder. This is a stand-in that lets the rerank step of
    the pipeline be exercised without an API key; a real reranker (e.g.
    Cohere) plugs in behind the same interface with no changes to the
    retrieval pipeline.
    """

    async def rerank(
        self, query: str, candidates: list[RerankCandidate]
    ) -> list[RerankResult]:
        query_tokens = _significant_tokens(query)
        if not query_tokens:
            return [RerankResult(id=c.id, score=0.0) for c in candidates]

        results = []
        for candidate in candidates:
            candidate_tokens = _significant_tokens(candidate.text)
            overlap = len(query_tokens & candidate_tokens)
            score = overlap / len(query_tokens)
            results.append(RerankResult(id=candidate.id, score=min(score, 1.0)))
        return results
