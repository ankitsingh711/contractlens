# RAG Architecture

> Status: not yet implemented (planned for Phase 3). This document records the design and rationale up front so Phase 3 implements against a decision, not a blank page.

## Why PostgreSQL + pgvector instead of a dedicated vector database

- **One database, one transaction model.** Document metadata, chunks, and their embeddings live in the same database as everything else (users, orgs, evaluations). A document upload, its chunks, and their vectors can be written in one transaction — no dual-write consistency problem between a relational store and a separate vector store.
- **Operationally simpler at this scale.** Contract corpora for a single enterprise customer are thousands to low millions of chunks, well within pgvector's practical range (especially with an HNSW index). A dedicated vector DB (Pinecone, Weaviate, Qdrant) becomes worth the extra moving part at a scale this project isn't targeting for its MVP.
- **It doesn't foreclose the alternative.** The retrieval layer is built behind an interface (`retrieval/`), so swapping the vector store later is a matter of implementing that interface against a different backend, not a rewrite. The "what happens at 1M+ documents" answer is: add a dedicated ANN store behind the same interface, or shard by organization.

## Why hybrid search (vector + keyword), not vector-only

Legal and contract text has exact-match terms that matter — defined terms, section numbers, party names, dollar amounts — where semantic similarity alone under- or over-retrieves. PostgreSQL full-text search (keyword/BM25-style) is combined with pgvector cosine similarity, and their scores are fused (planned: reciprocal rank fusion) before reranking. This is standard practice in production RAG systems because the two retrieval modes fail differently and cover for each other.

## Why document-aware chunking, not fixed-size splitting

Splitting every N characters ignores contract structure and produces chunks that cut a clause in half or merge two unrelated clauses. The planned chunker preserves page, section/subsection, heading, and clause boundaries detected during structure parsing, so each chunk is a coherent unit that can be cited on its own (page + section, not just a character offset).

## Why reranking

Vector + keyword fusion is a recall-oriented step (cast a wide net); a cross-encoder reranker is precision-oriented (score the fused candidates against the actual query). Separating them keeps the reranker abstraction swappable (`RERANKER_PROVIDER=cohere|mock`) without touching the fusion logic.

## Planned pipeline

```
Query → Understanding → Expansion → [Vector Search + Keyword Search] → Fusion → Reranking → Top-K → Evidence Filtering → LLM
```

Each stage will be implemented and tested independently in Phase 3, with retrieval-specific tests (recall/precision against the evaluation dataset in `evaluation/`) rather than only end-to-end tests.
