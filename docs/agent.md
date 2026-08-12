# Agent Architecture

> Status: not yet implemented (planned for Phase 4). This document records the design and rationale up front.

## Why LangGraph instead of a linear chain

A simple prompt-and-parse chain can't express the control flow this product needs: retrieve, check whether the evidence is actually sufficient, and only then decide between reasoning toward an answer or abstaining — with citation validation as a hard gate afterward, not a hope. That's a graph with a real branch, not a pipeline. LangGraph gives:

- **Explicit, typed state** (`AgentState`) threaded through every node, instead of implicit context stuffed into a prompt string.
- **A real conditional edge** between "enough evidence → reason" and "not enough evidence → abstain" — the abstention path is a first-class node, not a fallback wrapped around the happy path.
- **Inspectable steps.** Each node's input/output, latency, and token usage can be recorded independently, which is exactly what the Agent Runs UI needs to render (classification → planning → retrieval → reranking → evidence validation → reasoning → citation validation → response).

## Planned graph

```
START → classify_query → plan → retrieve → evaluate_evidence
                                                  │
                          ┌───────────────────────┴───────────────────────┐
                     enough evidence                                 insufficient
                          │                                               │
                        reason                                        abstain
                          │
                  validate_claims → validate_citations → final_response
```

## Typed state

```python
class AgentState(TypedDict):
    query: str
    document_ids: list[str]
    intent: str
    retrieved_chunks: list[dict]
    evidence_score: float
    answer: str | None
    citations: list[dict]
    confidence: float
    tool_calls: list[dict]
    errors: list[str]
```

## Why abstention is a designed node, not an afterthought

The product's stated priority order is accuracy > groundedness > safety > completeness > speed. An agent that always produces *an* answer optimizes completeness at the expense of groundedness. Abstention is implemented as a graph node reached via a real conditional edge from `evaluate_evidence`, so "I don't have enough evidence" is a normal, tested outcome — not an exception path.

## Why citation validation is a separate step after generation

Generation and grounding are different failure modes: an LLM can produce fluent text that cites a chunk it never actually used, or misquote a retrieved passage. `validate_citations` re-checks every citation the model emitted against the chunks that were actually retrieved for that run — a citation that doesn't trace back to a retrieved chunk is rejected before the response reaches the user, regardless of how confident the generated text sounds.

## Tools

Planned tools (`search_documents`, `search_contract`, `get_clause`, `get_document_metadata`, `calculate`, `compare_clauses`, `retrieve_source`) will each have a typed Pydantic input/output schema, explicit error handling, a timeout, and a logged invocation record — tool calls are part of the agent trace, not a black box.

## Prompt injection guardrail

Document content is untrusted input. Prompts are structured with explicit separation between system instructions, user query, retrieved document content, and tool output, and document text is never concatenated directly into the system/developer instruction region. A test case with an embedded "ignore previous instructions" payload in a document chunk is part of the Phase 4 test suite.
