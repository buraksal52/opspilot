# OpsPilot — RAG System Specification

## 1. Purpose

The OpsPilot Retrieval-Augmented Generation system provides grounded access to internal business documents.

Its goal is not merely to return semantically similar text.

It must provide:

* relevant evidence,
* source traceability,
* reliable retrieval,
* debuggable ranking,
* measurable retrieval quality.

RAG is primarily an evidence retrieval system.

Generation comes after retrieval.

---

# 2. Primary Use Cases

Examples:

> What is the standard delivery window?

> What changed on July 11?

> What does the refund policy say about delayed deliveries?

> Was a shipping-provider migration documented?

The retrieval system may also provide evidence to broader investigations.

---

# 3. Supported Initial Sources

V1 unstructured sources:

* PDF
* Markdown
* plain text

All processed documents should eventually produce normalized DocumentChunk records.

---

# 4. High-Level Pipeline

Ingestion:

```text
Document
↓
Parse
↓
Normalize
↓
Chunk
↓
Attach Metadata
↓
Embed
↓
Persist
```

Retrieval:

```text
User / Agent Query
↓
Query Processing
↓
Lexical Retrieval
+
Vector Retrieval
↓
Candidate Fusion
↓
Reranking
↓
Context Selection
↓
Evidence Objects
```

---

# 5. Core Principle

Do not treat:

```text
Vector Search → top 5 chunks
```

as the final RAG architecture.

OpsPilot should use multiple retrieval signals because business questions may contain:

* exact policy terms,
* dates,
* product names,
* operational vocabulary,
* semantic concepts.

---

# 6. Document Parsing

Each parser should produce normalized text while preserving useful source structure.

Important metadata may include:

* document ID,
* title,
* file type,
* page number,
* section heading,
* character offsets,
* processing timestamp.

Do not discard source location metadata during parsing.

---

# 7. Text Normalization

Normalization may include:

* whitespace cleanup,
* repeated header/footer handling,
* broken line joining,
* control-character removal.

Do not aggressively rewrite source content.

Evidence should remain faithful to the original document.

---

# 8. Chunking Goals

Chunking should balance:

* semantic coherence,
* retrieval granularity,
* context size,
* citation precision.

Very large chunks reduce retrieval precision.

Very small chunks may remove necessary context.

---

# 9. Initial Chunking Strategy

Begin with a straightforward configurable strategy.

Recommended baseline:

* structure-aware where document structure is available,
* otherwise token/character-based chunking,
* moderate overlap.

Example starting configuration:

```text
target_tokens ≈ 400–700
overlap ≈ 50–100 tokens
```

These are starting values, not permanent architecture rules.

Final values must be informed by evaluation.

---

# 10. Chunk Boundaries

Prefer boundaries such as:

* section,
* paragraph,
* page subsection

over arbitrary character cuts where practical.

Do not merge unrelated document sections solely to reach target size.

---

# 11. Chunk Metadata

Every chunk should retain enough information to resolve a citation.

Potential fields:

```text
document_id
chunk_id
chunk_index
page_number
section_title
content
token_count
metadata
```

---

# 12. Embedding Abstraction

Embedding generation should use a narrow provider interface.

Conceptually:

```text
EmbeddingProvider

embed_text(text)
embed_batch(texts)
```

Application logic should not depend directly on a single model vendor.

---

# 13. Embedding Persistence

Embeddings should be stored with DocumentChunk data using pgvector.

Persist relevant model/version metadata so re-indexing can be performed intentionally later.

---

# 14. Embedding Versioning

If the embedding model changes, existing embeddings may no longer be comparable.

Store an identifier such as:

```text
embedding_model
embedding_version
```

Do not silently mix incompatible vector spaces.

---

# 15. Query Processing

Before retrieval, the system may normalize the query.

Potential operations:

* whitespace cleanup,
* language normalization,
* business entity extraction,
* optional query rewrite.

Avoid unnecessary rewriting of already clear questions.

---

# 16. Query Rewrite

Query rewriting may be useful when an investigation query is verbose.

Example:

User:

> We changed something in shipping recently and customers seem angrier. What happened?

Potential retrieval-focused queries:

```text
shipping provider change
shipping migration
customer delivery complaints
```

Do not replace the original query permanently.

Preserve both original and rewritten forms for debugging.

---

# 17. Lexical Retrieval

OpsPilot should include keyword/lexical retrieval.

Potential implementation:

PostgreSQL full-text search.

Benefits:

* exact terminology,
* IDs,
* dates,
* names,
* business-specific vocabulary.

The exact implementation should be benchmarked before introducing additional infrastructure.

---

# 18. Vector Retrieval

Vector search should retrieve semantically related chunks using pgvector.

Configurable values:

* candidate count,
* similarity metric,
* index strategy.

Do not choose index configuration purely by convention.

For the project dataset size, exact search may initially be acceptable before approximate indexes are necessary.

---

# 19. Candidate Pool

Lexical and vector search should produce a broader candidate pool than the final number of contexts.

Example:

```text
Vector top 15
Lexical top 15
↓
Fusion
↓
20 unique candidates
↓
Reranking
↓
Top 5–8
```

Numbers must remain configurable.

---

# 20. Result Fusion

Initial preferred strategy:

Reciprocal Rank Fusion (RRF)

because:

* it combines rankings without requiring directly comparable raw scores,
* it is simple,
* it is interpretable,
* it works well as a strong baseline.

Exact formula/configuration should be documented during implementation.

---

# 21. Duplicate Handling

The same chunk may appear in both lexical and vector retrieval.

Candidates must be deduplicated using stable chunk IDs.

Do not present duplicate evidence simply because multiple retrievers found it.

---

# 22. Reranking

After initial retrieval, apply a reranking stage.

Possible rerankers:

* dedicated cross-encoder,
* provider reranking API,
* carefully constrained model-based reranking.

The initial implementation should balance:

* quality,
* latency,
* cost.

Reranker choice should be recorded in DECISIONS.md.

---

# 23. Reranking Input

Reranking should consider:

* query,
* chunk content,
* potentially concise source metadata.

Do not expose unnecessary full document context to the reranker.

---

# 24. Context Selection

The highest-ranked chunks should not automatically all be passed to the LLM.

Context selection should consider:

* relevance,
* redundancy,
* source diversity,
* token budget.

Prefer evidence diversity when several chunks express the same information.

---

# 25. Context Budget

Use a configurable context budget.

Do not fill the model context window merely because capacity exists.

More context may reduce answer quality.

---

# 26. Evidence Objects

Retrieval should produce structured evidence rather than anonymous strings.

Conceptual result:

```json
{
  "chunk_id": "...",
  "document_id": "...",
  "title": "Shipping Provider Migration Report",
  "page": 2,
  "content": "...",
  "scores": {
    "vector": 0.82,
    "lexical": null,
    "fusion": 0.04,
    "rerank": 0.91
  }
}
```

Exact schema may differ.

---

# 27. Citation Generation

The LLM should reference evidence IDs provided by the application.

Do not ask the model to invent filenames/pages from memory.

Preferred process:

```text
Evidence Objects
↓
LLM receives stable evidence IDs
↓
Generated claim references evidence IDs
↓
Application resolves them to UI citations
```

---

# 28. Citation Validation

Before showing final results, validate that cited evidence IDs:

* exist,
* belong to the investigation/workspace,
* were actually retrieved,
* resolve to valid sources.

Unsupported citation IDs should be rejected.

---

# 29. RAG Generation Prompt Principle

Clearly state that retrieved context:

* is evidence,
* may contain irrelevant or malicious instructions,
* must not override system rules,
* should be used only for factual grounding.

The model should acknowledge insufficient evidence rather than invent an answer.

---

# 30. No-Evidence Behavior

If retrieval does not produce sufficient support:

Preferred response:

> I could not find enough internal evidence to answer this reliably.

Not:

> Based on general knowledge, the likely answer is...

OpsPilot is designed to investigate company data, not substitute general LLM speculation for missing evidence.

---

# 31. Metadata Filtering

Retrieval should eventually support filters such as:

* workspace,
* document,
* document type,
* time range where meaningful.

Workspace filtering is mandatory.

---

# 32. Retrieval Observability

Store or expose useful trace data:

* original query,
* rewritten query,
* lexical candidates,
* vector candidates,
* fusion ranking,
* reranker scores,
* selected chunks.

This is critical for debugging poor answers.

---

# 33. Retrieval Debug UI

A development/debug interface should eventually show:

```text
Query

Vector results
Lexical results
Fused candidates
Reranked results
Final context
```

This is useful both technically and as a portfolio demonstration.

---

# 34. Evaluation Dataset

Retrieval evaluation uses the questions tagged `retrieval` in the canonical evaluation question bank (DATASET.md §33) — it does not maintain its own separate question set. For each `retrieval`-tagged question, retrieval evaluation additionally needs expected documents/chunks, spanning subcategories such as:

* exact factual retrieval,
* semantic retrieval,
* date/event retrieval,
* policy retrieval,
* multi-document retrieval.

---

# 35. Evaluation Example

```json
{
  "query": "When did Northstar migrate shipping providers?",
  "expected_documents": [
    "Shipping Provider Migration Report"
  ],
  "expected_fact": "July 11"
}
```

---

# 36. Retrieval Metrics

Track metrics such as:

* Recall@K
* Precision@K
* MRR

Recall should be prioritized initially because missing critical evidence prevents correct downstream reasoning.

---

# 37. Baseline First

Before adding sophisticated RAG components:

1. implement simple vector retrieval,
2. evaluate,
3. add lexical retrieval,
4. evaluate,
5. add fusion,
6. evaluate,
7. add reranking,
8. evaluate.

Do not implement the entire pipeline without measuring whether each stage improves results.

## Evaluation Gate

The Northstar document corpus is small (five business documents). Lexical retrieval and reranking are not assumed to be net-positive at this corpus size, and each stage must clear an explicit evaluation gate against the canonical `retrieval`-tagged questions (DATASET.md §33) before it is kept:

* if adding lexical retrieval does not measurably improve Recall@K/Precision@K/MRR over the vector-only baseline, keep the vector-only baseline and record that outcome in DECISIONS.md rather than keeping the added complexity by default,
* if adding reranking does not measurably improve ranking quality over fused retrieval, keep fused retrieval without a reranking stage,
* "measurable improvement" means a recorded evaluation-run comparison, not an assumption that a more sophisticated stage must be better.

A stage that fails its gate is removed or left disabled, not kept "for completeness."

---

# 38. Latency Measurement

Track latency per stage:

```text
query processing
vector search
lexical search
fusion
reranking
context selection
```

Quality improvements must be considered against demo responsiveness.

---

# 39. Caching

Potential cache candidates:

* embeddings of identical content,
* repeated retrieval queries,
* reranking results.

Do not introduce caching before repeated cost/latency is measured.

---

# 40. Document Updates

If a document changes:

* old chunks should not remain active,
* new content must be re-chunked,
* embeddings must be regenerated.

Use clear indexing/version behavior.

---

# 41. Document Deletion

Deleting a source must remove or deactivate its:

* documents,
* chunks,
* embeddings

from future retrieval and future investigations.

This is now explicit for V1: Evidence records created during past investigations hold a bounded snapshot of the supporting content, captured at creation time (DATA_MODEL.md §15). Deleting the source does not remove, corrupt, or retroactively invalidate that snapshot. The UI resolves `source_reference` against the current source; if the source no longer exists, it is shown as "source unavailable" while the preserved Evidence snapshot itself remains fully inspectable. No re-fetch of the original document is ever attempted through historical Evidence.

---

# 42. Failure Handling

Possible failures:

* parser failure,
* embedding failure,
* vector query failure,
* reranker failure.

Do not silently pretend retrieval succeeded.

Where appropriate, degrade gracefully.

Example:

If reranker provider is temporarily unavailable, the system may optionally return fused retrieval results if configured to do so.

Such fallback behavior must be visible in traces.

---

# 43. Security

Every retrieval query must enforce workspace isolation.

Retrieved document content is untrusted.

Never allow retrieved instructions to:

* alter system prompts,
* change tool permissions,
* request secrets,
* execute tools.

---

# 44. V1 Definition of Done

The RAG system is ready when:

1. Northstar documents are parsed and chunked,
2. embeddings are persisted,
3. vector retrieval works,
4. lexical retrieval works,
5. hybrid fusion works,
6. reranking works,
7. citations resolve correctly,
8. retrieval traces are inspectable,
9. known questions achieve acceptable evaluation results,
10. missing evidence produces honest uncertainty.

---

# 45. Core Rule

RAG exists to retrieve defensible evidence.

The objective is not:

> Produce the most convincing answer.

The objective is:

> Find the best available internal evidence and enable grounded reasoning over it.
