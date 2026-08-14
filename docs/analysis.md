# Risk Analysis & Document Comparison

> Status: implemented (Phase 5 — see `app/services/risk_analysis_service.py`, `app/services/comparison_service.py`, `app/services/risk_categories.py`).

## Why a fixed category list with per-category retrieval, not one open-ended pass

An LLM asked to "find the risks in this contract" in one shot has no structure forcing it to actually look for termination, indemnification, liability, *and* SLA terms — it will tend to surface whatever's most salient and silently skip the rest. Risk analysis here instead runs the same evidence pipeline **once per category** (12 fixed categories, each with its own retrieval query — see `RISK_CATEGORIES` in `app/services/risk_categories.py`), so every category gets an independent, evidence-gated chance to produce a finding. This also means the absence of a finding for e.g. "indemnification" is meaningful — it means retrieval found nothing above threshold for that category in that document — rather than the LLM just not getting around to it.

## Why a category with no evidence produces no finding at all

The product's explicit requirement is "never generate a risk without evidence." This is enforced the same way abstention is enforced in the chat agent (`docs/agent.md`): a category is skipped, not guessed, if (a) hybrid search returns no chunks or the evidence score is below `EVIDENCE_THRESHOLD`, or (b) the LLM's generated summary ends up with zero citations after `validate_citations()` strips unsupported markers. Both are the same code paths used for Q&A abstention — risk analysis is not a separate, less-guarded pipeline.

## Why severity is a keyword heuristic, not a learned/prompted classifier

Two options were available: ask the LLM to output a structured severity label, or scan the retrieved evidence text for known escalating/mitigating language ("unlimited"/"uncapped" vs. "capped at"/"limited to"). The heuristic was chosen because it's provider-agnostic — it works identically whether `LLM_PROVIDER` is `mock` or a real model, since it doesn't depend on the model reliably emitting structured output — and because it's directly testable and explainable (`tests/test_risk_analysis.py::test_analyze_document_flags_unlimited_liability_as_high_severity` asserts the exact behavior). This is a documented simplification, not a claim of a trained risk model: see the README's trade-offs section for its known limitation (it won't catch risk phrased outside its keyword lists).

## Why comparison shows retrieved text, not an LLM-normalized value

Risk analysis generates a natural-language summary (with citation validation as the safety net). Document comparison deliberately does **not** — each cell in the comparison table is the literal top-retrieved chunk for that category in that document, unprocessed by an LLM. Comparison is inherently about precise differences ("30 days" vs. "7 days"), which is exactly the kind of detail an LLM summarization step can silently round away or misstate. Showing the retrieved text directly means the comparison can never be less accurate than the retrieval it's built on.

## Why comparison uses semantic search per document, not the same section number

Two different contracts number their termination clause differently — "8.2" in one, "5" in another. Reusing the Phase 4 `compare_clauses` tool's exact-section-match behavior wouldn't line up related clauses across differently-structured documents. Document comparison instead runs the same category search queries used by risk analysis against each document independently, aligning by semantic category rather than by section number.

## Why the risk score is a simple weighted average, not a black-box model

`risk_score = round(100 * mean(severity_weight))` over the categories that actually produced a finding (high=1.0, medium=0.55, low=0.2). This is transparent and reproducible — given the same findings, anyone can recompute the score by hand — which matters more for a compliance-facing feature than a marginally more sophisticated but opaque scoring function would.
