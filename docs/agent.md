# Agent Architecture

> Status: implemented (Phase 4 — see `apps/api/app/agents/`: `graph.py`, `nodes.py`, `state.py`, `tools/`, and `apps/api/app/services/agent_service.py` for persistence/tracing). Not yet implemented: LLM-based query classification/planning (currently heuristic — see below) and true token-level streaming from the LLM (the SSE stream is step-level, not token-level).

## Why LangGraph instead of a linear chain

A simple prompt-and-parse chain can't express the control flow this product needs: retrieve, check whether the evidence is actually sufficient, and only then decide between reasoning toward an answer or abstaining — with citation validation as a hard gate afterward, not a hope. That's a graph with a real branch, not a pipeline. LangGraph gives:

- **Explicit, typed state** (`AgentState`) threaded through every node, instead of implicit context stuffed into a prompt string.
- **A real conditional edge** between "enough evidence → reason" and "not enough evidence → abstain" — the abstention path is a first-class node, not a fallback wrapped around the happy path.
- **Inspectable steps.** Each node's output and latency is recorded independently (via `graph.astream(state, stream_mode="updates")` in `agent_service.stream_agent`), which is exactly what the Agent Runs UI renders (classification → planning → retrieval → evidence validation → reasoning/abstention → claim validation → citation validation → final response).

## The graph, as built

```
START → classify_query → plan → retrieve → evaluate_evidence
                                                  │
                          ┌───────────────────────┴───────────────────────┐
                     enough evidence                                 insufficient
                          │                                               │
                        reason                                        abstain
                          │                                               │
                  validate_claims                                        │
                          │                                               │
                          └───────────────────► validate_citations ◄──────┘
                                                  │
                                            final_response → END
```

This is exactly `apps/api/app/agents/graph.py` — nine nodes, one conditional edge (`route_on_evidence`), both the `reason` and `abstain` branches converging on `validate_citations` before `final_response`.

## Typed state

```python
class AgentState(TypedDict):
    query: str
    organization_id: str
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

(`organization_id` was added to the originally-sketched shape once tool calls needed org-scoping context available in state, not just closed over by the node functions.)

## Why abstention is a designed node, not an afterthought

The product's stated priority order is accuracy > groundedness > safety > completeness > speed. An agent that always produces *an* answer optimizes completeness at the expense of groundedness. Abstention is a graph node (`abstain`) reached via a real conditional edge from `evaluate_evidence` (`route_on_evidence`, gated on `EVIDENCE_THRESHOLD`), so "I don't have enough evidence" is a normal, tested outcome — not an exception path. See `tests/test_agent_graph.py::test_graph_abstains_on_insufficient_evidence`.

## Why citation validation is a separate step after generation

Generation and grounding are different failure modes: an LLM can produce fluent text that cites a chunk it never actually used, or misquote a retrieved passage. `validate_citations_node` (wrapping `app/services/citations.py::validate_citations`) re-checks every `[n]` marker the model emitted against the chunks that were actually retrieved for that run — a marker that doesn't resolve to a retrieved chunk is stripped before the response reaches the user. If **zero** citations survive, the node overwrites the answer with the abstention message: an unsupported answer is never shown just because generation didn't literally fail.

## Why `validate_claims` exists as a separate node from `validate_citations`

They catch different things. `validate_citations` is a hard, mechanical gate: does marker `[n]` point at a chunk that was actually retrieved? `validate_claims` is a softer faithfulness signal: does *every sentence* in the answer carry a citation, or did the model slip in an uncited claim alongside cited ones? The current implementation is a heuristic (sentence-splitting + regex for `[\d+]`) that records a warning into `state["errors"]` rather than blocking the response — visible in the Agent Runs trace so a reviewer can see "this answer had an uncited sentence" even though the hard citation gate still passed. A stronger version (e.g. an NLI-based entailment check per sentence) is a natural upgrade behind the same node.

## Tools

Implemented (`app/agents/tools/`): `search_documents` (wraps the Phase 3 hybrid retrieval pipeline), `get_clause` (exact section lookup within one document), `get_document_metadata`, `calculate` (arithmetic only — parsed via Python's `ast` module, not `eval`, so it can never execute arbitrary code; see `tests/test_agent_tools.py` for injection-attempt tests), `retrieve_source` (full chunk + document context for a citation), and `compare_clauses` (same-section lookup across two documents — the building block Phase 5's document comparison feature calls).

Every tool has a typed Pydantic input/output schema, and every call goes through `run_tool()` (`app/agents/tools/base.py`), which adds a 10s timeout, structured logging, and error containment — a failing tool becomes a recorded `ToolCallRecord.error` on the agent state, not an unhandled exception that kills the run. Every tool is also **org-scoped at the SQL level** (each tool's query filters by `organization_id`), so the agent can never read another organization's documents through a tool call regardless of what a (future, LLM-driven) planner asks for.

### Why tool selection is currently heuristic, not LLM function-calling

`plan()` decides which tool(s) to call using keyword/regex heuristics on `intent` and the query text (e.g., a "compare" query with 2+ document IDs plans a `compare_clauses` call in addition to `search_documents`). This is an honest simplification: `OpenAILLMProvider` doesn't yet implement function-calling, and the mock LLM provider has no reasoning to select tools with. Because tool selection lives entirely in `plan()`, swapping in a real LLM-driven planner (the model decides which tools to call, agent-style) is a change scoped to that one function — the rest of the graph, the tool registry, and the trace/persistence layer don't need to change.

## Prompt injection guardrail

Document content is untrusted input. The QA prompt (`prompts/qa/v1.txt`) places SYSTEM INSTRUCTIONS before an explicitly labeled EVIDENCE section and instructs the model to treat evidence as data, never as commands — see `tests/test_prompt_injection.py` for the structural test (the boundary always holds) and the citation-marker-smuggling test (a fake `[n]` embedded in document text is never treated as a real citation). This guardrail was built in Phase 3 and reused as-is by the agent's `reason` node in Phase 4 — the agent didn't need a separate mechanism.

## Persistence and tracing

Every run creates one `AgentRun` row and one `AgentStep` row per graph node (`app/services/agent_service.py::stream_agent`), which is what `GET /api/agent-runs/{id}` and the `/agent-runs/[id]` trace UI render. The same function also creates/updates a `Conversation` and appends the user/assistant `Message` pair, so conversation history and agent traces are two views over the same underlying run — not two separately-maintained records that can drift.

### Why the API streams via SSE, not just returning JSON

`POST /api/chat` streams one SSE event per completed graph node (`run_started` → `step` × N → `done`/`error`) instead of blocking until the whole run finishes. This is what lets the Agent Runs-style trace show up *live* in the AI Assistant UI (see `hooks/use-chat.ts`'s `currentStepLabel`) instead of a bare loading spinner — the user sees "Searching documents… Evaluating evidence… Generating answer…" as it happens. Token-level streaming from the LLM itself is not implemented; each `reason` step still waits for the full completion before yielding its event, which is an accurate reflection of `LLMProvider.complete()`'s current (non-streaming) interface rather than a limitation of the SSE transport.
