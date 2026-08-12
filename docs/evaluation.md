# Evaluation Strategy

> Status: not yet implemented (planned for Phase 6). This document records the design and rationale up front.

## Why evaluation is a first-class system, not a manual spot-check

"It looked right when I tried it" doesn't scale and doesn't survive a prompt or model change. The product's core claim — that answers are grounded and the system knows when it doesn't know — has to be measurable, or it's just a claim. Phase 6 builds a dataset of 50+ question/expected-answer/expected-source test cases (`evaluation/datasets/`) and an automated harness that scores every run against it.

## Metrics

- **Faithfulness** — does the generated answer only state what the evidence supports?
- **Citation accuracy** — do cited sources actually contain the cited claim?
- **Retrieval recall / precision** — did retrieval surface the chunks needed to answer, without excessive noise?
- **Hallucination rate** — fraction of claims not traceable to evidence.
- **Answer relevance** — does the answer address the question asked?
- **Latency, token usage, estimated cost** — production concerns tracked alongside correctness, not separately.

## Why regression testing, not just a one-time score

A prompt tweak, a model swap, or a retrieval change can silently regress groundedness even while looking fine on a handful of manual tests. Every evaluation run is compared against a stored baseline; a drop past a threshold on any metric is flagged as a regression before it ships. This is the same discipline as a test suite gating a merge, applied to model/prompt/retrieval behavior instead of code correctness alone.

## Why prompts are versioned files, not inline strings

Prompts are the part of an LLM system most likely to change under iteration. Versioning them as files (`prompts/<task>/v1.txt`, `v2.txt`, ...) and recording the prompt version used on every agent run means a regression can be traced to *which* prompt version caused it, and a rollback is a config change, not a code change.
