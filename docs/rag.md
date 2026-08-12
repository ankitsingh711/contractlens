# RAG Architecture

> Status: chunking, embeddings, and storage are implemented (Phase 2 — see `app/services/parsing/`, `app/services/embeddings/`). Retrieval (hybrid search, fusion, reranking) is planned for Phase 3. This document records the design and rationale up front so each phase implements against a decision, not a blank page.

## Why PostgreSQL + pgvector instead of a dedicated vector database

- **One database, one transaction model.** Document metadata, chunks, and their embeddings live in the same database as everything else (users, orgs, evaluations). A document upload, its chunks, and their vectors can be written in one transaction — no dual-write consistency problem between a relational store and a separate vector store.
- **Operationally simpler at this scale.** Contract corpora for a single enterprise customer are thousands to low millions of chunks, well within pgvector's practical range (especially with an HNSW index). A dedicated vector DB (Pinecone, Weaviate, Qdrant) becomes worth the extra moving part at a scale this project isn't targeting for its MVP.
- **It doesn't foreclose the alternative.** The retrieval layer is built behind an interface (`retrieval/`), so swapping the vector store later is a matter of implementing that interface against a different backend, not a rewrite. The "what happens at 1M+ documents" answer is: add a dedicated ANN store behind the same interface, or shard by organization.

## Why hybrid search (vector + keyword), not vector-only

Legal and contract text has exact-match terms that matter — defined terms, section numbers, party names, dollar amounts — where semantic similarity alone under- or over-retrieves. PostgreSQL full-text search (keyword/BM25-style) is combined with pgvector cosine similarity, and their scores are fused (planned: reciprocal rank fusion) before reranking. This is standard practice in production RAG systems because the two retrieval modes fail differently and cover for each other.

## Why document-aware chunking, not fixed-size splitting

Splitting every N characters ignores contract structure and produces chunks that cut a clause in half or merge two unrelated clauses. The chunker (`app/services/parsing/chunker.py`) instead:

1. Splits text into paragraphs on blank lines (not a fixed character count).
2. Detects section headers with two regex families — numbered (`8.2 Termination`, `8.2. Termination for Cause`) and labeled (`ARTICLE VIII - TERMINATION`, `SECTION 8: TERMINATION`) — common to contract drafting conventions.
3. Tags every subsequent paragraph with the most recently seen section/heading until the next one appears, so a clause's chunk always carries its section number and heading, not just its raw text.
4. Splits paragraphs that exceed the token budget (220 tokens) on sentence boundaries (`. ` / `; `) rather than mid-sentence, and merges paragraphs under the minimum (20 tokens, e.g. a lone heading or a trailing signature line) into their neighbor so no chunk is a near-empty fragment.

Each chunk is therefore a coherent, independently citable unit (page + section + heading), which is what makes the citation UI in Phase 3 possible — a citation points at something a human can actually verify, not an arbitrary character range.

**Known limitation**: this is regex-based structure detection, not a layout-aware ML parser. It handles the numbered/labeled heading styles common in contracts but will miss unconventional formatting (e.g. headings styled only by bold/font-size with no numbering, in a source format that doesn't preserve that styling as extractable text). A learned document-structure model is a reasonable future upgrade behind the same chunker interface.

## Why reranking

Vector + keyword fusion is a recall-oriented step (cast a wide net); a cross-encoder reranker is precision-oriented (score the fused candidates against the actual query). Separating them keeps the reranker abstraction swappable (`RERANKER_PROVIDER=cohere|mock`) without touching the fusion logic.

## What's already in place for retrieval to build on

The Phase 2 migration creates both indexes hybrid search needs, even though nothing queries them yet:

- An **HNSW index** (`vector_cosine_ops`) on `document_chunks.embedding` for approximate nearest-neighbor vector search.
- A **generated `tsvector` column with a GIN index** (`to_tsvector('english', text)`, `STORED`) on `document_chunks.text` for PostgreSQL full-text (keyword) search.

The embedding provider is already abstracted (`app/services/embeddings/`): `MockEmbeddingProvider` (deterministic hashed bag-of-words — see `docs/agent.md`-adjacent trade-off notes in the README) for demo mode, `OpenAIEmbeddingProvider` for real use, selected by `EMBEDDING_PROVIDER`. Phase 3 writes the retrieval logic that queries these two indexes and fuses their results — no further schema changes should be needed.

## Planned pipeline

```
Query → Understanding → Expansion → [Vector Search + Keyword Search] → Fusion → Reranking → Top-K → Evidence Filtering → LLM
```

Each stage will be implemented and tested independently in Phase 3, with retrieval-specific tests (recall/precision against the evaluation dataset in `evaluation/`) rather than only end-to-end tests.
