# OpsPilot — Implementation Backlog

## 1. Purpose

ROADMAP.md defines major development phases.

This file translates those phases into actionable engineering tasks.

Rules:

* work in order unless explicitly reprioritized,
* P0 tasks block later core work,
* check tasks only after Definition of Done is satisfied,
* avoid implementing future-phase features early,
* update this backlog as implementation reveals new necessary work.

---

# Phase 0 — Specification

## P0

* [x] Create CLAUDE.md
* [x] Create PRODUCT.md
* [x] Create ARCHITECTURE.md
* [x] Create ROADMAP.md
* [x] Create DATA_MODEL.md
* [x] Create DATASET.md
* [x] Create DECISIONS.md
* [x] Create API.md
* [x] Create TESTING.md
* [x] Create SECURITY.md
* [x] Create RAG_SYSTEM.md
* [x] Create ANALYTICS_ENGINE.md
* [x] Create AGENT_SYSTEM.md
* [x] Create BACKLOG.md

## Remaining Phase 0 Gate

* [x] Run cross-document architecture review
* [x] Resolve specification contradictions
* [x] Confirm dependencies required for Phase 1 — resolved: ADR-019 (authentication: email/password, Argon2/pwdlib, JWT/PyJWT) and ADR-020 (database/ORM: PostgreSQL + SQLAlchemy 2.x + Alembic)
* [x] Confirm initial repository layout — resolved: ADR-021, approved structure recorded in ARCHITECTURE.md §6
* [x] Mark Phase 0 complete

---

# Phase 1 — Project Foundation

## 1.1 Repository

* [x] Create frontend application under `apps/web/`
* [x] Create backend application under `apps/api/app/` with `api/`, `core/`, `domain/`, `application/`, `infrastructure/` (ADR-021) — create each subpackage when it has its first real file, not all five empty upfront
* [x] Establish root project structure per ADR-021 (`apps/`, `scripts/`, `infra/`, `tests/`, `docs/`)
* [x] Add .gitignore
* [x] Add .env.example (include JWT signing secret and database URL placeholders)
* [x] Add basic developer scripts/commands

---

## 1.2 Backend Foundation

* [x] Initialize FastAPI
* [x] Add application settings/configuration
* [x] Configure environment loading
* [x] Add health endpoint
* [x] Add structured application logging
* [x] Add common error-response structure
* [x] Add initial dependency layout

---

## 1.3 PostgreSQL

* [x] Add PostgreSQL service
* [x] Configure application database connection (SQLAlchemy 2.x async engine, ADR-020)
* [x] Configure Alembic migrations
* [x] Create `app` schema strategy
* [x] Create `analytics` schema strategy (no Alembic-managed tables here — per-Dataset tables are created programmatically per ADR-017/020)
* [x] Verify migrations from clean database

---

## 1.4 Foundational Models & Authentication

* [x] Implement User model (including `hashed_password`, ADR-019)
* [x] Implement Workspace model (`owner_id` as the V1 authorization anchor, ADR-019)
* [x] Add database constraints
* [x] Add migrations
* [x] Add repository/service boundaries where justified
* [x] Implement password hashing/verification using pwdlib (Argon2)
* [x] Implement JWT issuance/verification using PyJWT
* [x] Implement login endpoint (`POST /api/v1/auth/login`)
* [x] Implement auth dependency that resolves the current user from the `Authorization: Bearer` header for protected routes
* [x] Implement workspace-ownership authorization check (`Workspace.owner_id`) as a reusable dependency
* [x] Add tests: login success/failure, invalid/expired token rejection, cross-workspace access denial

---

## 1.5 Redis

* [x] Add Redis service to local environment
* [x] Add application Redis configuration
* [x] Add health/connectivity verification
* [x] Do not implement caching/jobs yet without need

---

## 1.6 Frontend Foundation

* [x] Initialize Next.js + TypeScript
* [x] Configure Tailwind
* [x] Configure shadcn/ui
* [x] Create application shell
* [x] Create navigation
* [x] Create base dashboard route
* [x] Connect frontend to backend health endpoint

---

## 1.7 Docker

* [x] Create backend Dockerfile
* [x] Create frontend Dockerfile
* [x] Create Docker Compose setup
* [x] Include PostgreSQL
* [x] Include Redis
* [x] Verify clean local startup

---

## 1.8 Phase 1 Tests

* [x] Backend health test
* [x] Database integration test
* [x] Workspace persistence test
* [x] Basic frontend/API connectivity verification

---

## Phase 1 Definition of Done

* [x] `docker compose up` starts required services
* [x] API health endpoint works
* [x] frontend reaches backend
* [x] PostgreSQL migrations work
* [x] Workspace persists
* [x] tests pass
* [x] relevant docs updated

---

# Phase 2 — Northstar Dataset

## 2.1 Dataset Generator Architecture

* [x] Create deterministic generation package/script — `scripts/northstar/` (ADR-023)
* [x] Define fixed random seed — `GeneratorConfig.seed` (`random.Random(seed)`, no global random state)
* [x] Define generator configuration — `northstar/config.py::GeneratorConfig`
* [x] Add output directory structure — `data/northstar/{csv,documents,eval,private}/` (gitignored, regenerated via `make generate-northstar`, ADR-023)

---

## 2.2 Customers

* [x] Generate customer IDs
* [x] Generate customer segments
* [x] Generate acquisition channels
* [x] Generate geographic attributes
* [x] Generate derived lifetime metrics where appropriate — `lifetime_orders`/`lifetime_value` computed from actual generated orders, not independently randomized

---

## 2.3 Products

* [x] Generate product catalog
* [x] Generate categories
* [x] Generate pricing
* [x] Generate costs
* [x] Validate product IDs

---

## 2.4 Orders

* [x] Generate June–July order timeline
* [x] Generate customer/product relationships
* [x] Model SwiftShip baseline (mean ~2.8 days)
* [x] Introduce July 11 RapidShip migration (traffic share + delivery-time shift)
* [x] Generate delivery-time distributions
* [x] Generate delays
* [x] Generate order values
* [x] Generate statuses

---

## 2.5 Refunds

* [x] Generate baseline refund behavior
* [x] Increase late-delivery refund probability after incident
* [x] Preserve unrelated refund reasons
* [x] Generate refund amounts
* [x] Maintain order/customer relationships

---

## 2.6 Support Tickets

* [x] Generate baseline ticket volume
* [x] Generate ticket categories
* [x] Generate realistic ticket text variation
* [x] Increase shipping complaints after incident
* [x] Generate sentiment
* [x] Generate resolution time

---

## 2.7 Business Documents

* [x] Create Refund Policy
* [x] Create Shipping Policy
* [x] Create Customer Support Handbook
* [x] Create Shipping Provider Migration Report
* [x] Create July Operations Incident Report

---

## 2.8 Ground Truth

* [x] Generate private ground_truth.json
* [x] Record incident date
* [x] Record expected patterns
* [x] Ensure runtime application never reads this as evidence — lives under `data/northstar/private/`, gitignored, not imported by any `apps/api` code

---

## 2.9 Validation

* [x] Validate dataset relationships
* [x] Validate provider migration timing
* [x] Validate delivery-time increase
* [x] Validate ticket increase
* [x] Validate refund increase
* [x] Validate realistic noise
* [x] Produce validation summary — `data/northstar/private/validation_report.json` + stdout; `generate.py` refuses to write output if any check fails

---

## Phase 2 Definition of Done

* [x] all files can be generated reproducibly — verified: two runs with the default seed produce byte-identical CSV/ground-truth output
* [x] relationships are valid — enforced by `northstar.validate` + `tests/unit/test_northstar_generator.py`
* [x] the migration event is represented in documents
* [x] the intended analytical signals exist
* [x] signals contain realistic noise
* [x] the primary conclusion can be independently verified (`ground_truth.json`, computed from actual data)
* [x] at least five useful investigations are supported — canonical `evaluation_questions.json` (DATASET.md §33), 18 questions across retrieval/analytics/agent/e2e
* [x] no application code needs hardcoded knowledge of the answer — `apps/api` does not reference `scripts/northstar` or `data/northstar` at all

---

# Phase 3 — Data Ingestion

## 3.0 Background Worker Decision (supersedes ADR-018)

* [x] Evaluate background worker technology options against actual Phase 3/4 workloads (PDF parsing, embedding generation) — ADR-024
* [x] Record the decision as a new ADR that supersedes ADR-018 — ADR-024: arq selected, activation deferred to Phase 4
* [x] Confirm Phase 1/2 work does not implicitly depend on a specific worker implementation — Phase 3 ingestion also runs synchronously, no worker dependency introduced yet

---

## 3.1 DataSource Domain

* [x] Implement DataSource model — `app/domain/data_source.py`
* [x] Implement status enum — `DataSourceStatus` (UPLOADED/PROCESSING/READY/FAILED/DELETED)
* [x] Add migration — `ad6b9ab586dc_add_data_sources_documents_and_datasets_.py`
* [x] Add application service — `application/ingestion/upload_service.py`
* [x] Add tests — `tests/api/test_data_source_upload.py`

---

## 3.2 Upload API

* [x] Implement multipart upload endpoint — `POST /api/v1/workspaces/{workspace_id}/data-sources/upload`
* [x] Validate file size — streamed read aborts past `upload_max_size_bytes` (SECURITY.md §20)
* [x] Validate MIME/file format — extension allowlist + PDF magic-byte check; see `upload_validation.py` docstring for why client-supplied Content-Type is recorded but not gated on
* [x] Sanitize handling of filenames — storage key built only from workspace/data-source UUIDs, never the filename (SECURITY.md §21)
* [x] Persist DataSource — `DataSourceRepository.create`
* [x] Handle failures — validation failures reject before persistence (422); parser failures persist as `DataSource.status = FAILED` with `error_message`

---

## 3.3 Document Ingestion

* [x] Implement Document model — `app/domain/document.py`
* [x] Implement PDF parser — `infrastructure/parsers/pdf_parser.py` (pypdf)
* [x] Implement Markdown parser — `infrastructure/parsers/markdown_parser.py`
* [x] Implement plain-text parser — `infrastructure/parsers/text_parser.py`
* [x] Normalize extracted text — `infrastructure/parsers/base.py::normalize_text`
* [x] Preserve source metadata — per-page text kept in `Document.metadata.pages`
* [x] Add parser tests — `tests/unit/test_document_parsers.py`

---

## 3.4 Dataset Ingestion

* [x] Implement Dataset model (per ADR-017: `physical_table_name` generated by the application, distinct from user-facing `name`) — `app/domain/dataset.py`
* [x] Parse CSV safely — `infrastructure/parsers/csv_parser.py` (size/row/column/cell bounds, ragged-row and duplicate-header rejection)
* [x] Infer column types — `infrastructure/analytics/type_inference.py`
* [x] Generate sanitized physical column identifiers (never derived directly from CSV header text) — `infrastructure/analytics/identifiers.py`
* [x] Create per-Dataset analytics table under `analytics.*` using only generated physical identifiers — `infrastructure/analytics/table_builder.py` (SQLAlchemy Core, ADR-020)
* [x] Insert rows — parameterized bulk insert, same table_builder module
* [x] Generate schema_definition with both `display_name` and `physical_name` per column — `Dataset.schema_definition`
* [x] Generate basic profile statistics — `infrastructure/analytics/profiling.py`
* [x] Add ingestion tests, including tests for malicious/SQL-metacharacter column headers — `tests/unit/test_identifier_injection.py` + `tests/api/test_data_source_upload.py::test_malicious_csv_header_round_trips_safely_through_real_postgres` (verified against a real Postgres `information_schema` query, not just in-process)

---

## 3.5 Data Source UI

* [x] Create Data Sources page — `apps/web/src/app/data-sources/page.tsx`
* [x] Add upload interface — native file input + FormData upload
* [x] Show processing states — status badges (READY/PROCESSING/FAILED/etc.); processing is synchronous per ADR-024 so the UI reflects the final state rather than a live in-flight spinner
* [x] Show source metadata — source type, filename, size, error message
* [x] Add delete flow — soft-delete via DELETE endpoint, removed from the list view

---

## Phase 3 Definition of Done

Per ROADMAP.md §7: "Northstar structured and unstructured data can be loaded into OpsPilot through real ingestion flows."

* [x] verified against the real system, not just tests: manually uploaded actual `data/northstar/csv/refunds.csv` (846 rows) and `data/northstar/documents/Refund Policy.pdf` through the live API against real Postgres — analytics table `analytics.ds_<uuid>` created with correct inferred types (`datetime`, `decimal`, `string`) and all 846 rows present; PDF text extracted correctly into `app.documents`
* [x] malicious CSV header (`"; DROP TABLE analytics.orders; --`) round-tripped safely end-to-end against real Postgres — confirmed via `information_schema` that only `ds_*`/`col_*` identifiers exist, never the malicious text
* [x] cross-workspace access denial verified (data source access, not just workspace access)
* [x] frontend build + lint pass (`npm run build`, `npm run lint`); pages manually smoke-tested via curl against the live dev server (no interactive browser session was available this session — see summary)
* [x] `make test-api`: 95/95 passing (16 Phase 1 + 12 Phase 2 + 67 Phase 3)

---

# Phase 4 — RAG

## 4.1 DocumentChunk

* [x] Implement DocumentChunk model — `app/domain/document_chunk.py` + `infrastructure/database/models/document_chunk.py` (`app` schema, per DATA_MODEL.md §2 ERD)
* [x] Add pgvector extension — `CREATE EXTENSION IF NOT EXISTS vector` in the new migration; Postgres image switched to `pgvector/pgvector:pg16` in `docker-compose.yml` and `Makefile` (ADR-026, since plain `postgres:16-alpine` doesn't ship it)
* [x] Add vector column — `embedding: Vector(768)`, nullable (filled asynchronously by the arq embedding job, ADR-026), dimension fixed by ADR-025
* [x] Add migration — `e3a1c9f4b2d7_add_document_chunks_table.py`, verified against a real `pgvector/pgvector:pg16` container via `make test-api` (100/100 passing, including new `tests/integration/test_document_chunk_repository.py` covering bulk-create, missing-embedding lookup, cosine-distance ranking, and cross-workspace isolation)

---

## 4.2 Chunking

* [x] Implement baseline chunking strategy — `app/application/retrieval/chunking_service.py`: page-structure-aware for PDF (`Document.metadata["pages"]`), paragraph-based fallback for Markdown/text, target/overlap tokens from settings, oversized-paragraph word-packing fallback; wired synchronously into `DocumentIngestionService.ingest()` (ADR-026 — chunking is CPU-only, stays sync)
* [x] Preserve page metadata — a chunk never spans two PDF pages (page atomicity enforced for citation precision, RAG_SYSTEM.md §8/§10)
* [x] Preserve section metadata where available — Markdown `#`/`##`/... headings become `section_title`, carried until the next heading; left `None` for PDF (no heading syntax survives text extraction, so not fabricated)
* [x] Track token counts — approximate chars/4 heuristic (`estimate_token_count`), documented in ADR-025 as a sizing estimate, not an exact provider token count
* [x] Add deterministic chunking tests — `tests/unit/test_chunking.py` (no content loss, determinism, overlap, page/section metadata, oversized-paragraph splitting) + `tests/api/test_data_source_upload.py::test_upload_pdf_creates_document_chunks` (real API + real Postgres, verifies chunks are created and unembedded after upload)

---

## 4.3 Embeddings

* [x] Define EmbeddingProvider interface — `infrastructure/embeddings/base.py` (`EmbeddingProvider` Protocol, `EmbeddingTaskType`, ADR-025)
* [x] Implement initial provider — `infrastructure/embeddings/gemini_provider.py` (Google Gemini `gemini-embedding-001`, ADR-025) + `infrastructure/embeddings/fake_provider.py` (deterministic, used by all automated tests per TESTING.md §30)
* [x] Implement batch embedding — bounded batch size (32) inside `GeminiEmbeddingProvider.embed_batch`
* [x] Store embedding model metadata — `DocumentChunk.embedding_model`/`embedding_version` set by `EmbeddingGenerationService` (`application/retrieval/embedding_service.py`)
* [x] Handle failures — bounded retry on transient errors only (5xx, 429), immediate raise as `EmbeddingProviderError` otherwise (ARCHITECTURE.md §22); background execution via arq (ADR-024/ADR-026, `infrastructure/jobs/{worker,tasks,queue}.py`), enqueued from `UploadService` after synchronous chunk creation
* [x] Add tests — `tests/unit/test_embedding_provider_contract.py`, `tests/unit/test_gemini_embedding_provider.py` (mocked client — success, server-error retry, rate-limit retry, non-transient no-retry, retry exhaustion), `tests/integration/test_embedding_job.py` (real Postgres/Redis — end-to-end generate_for_document + real arq enqueue). Additionally verified manually against a real `docker compose up` stack (worker container consumed a real enqueued job for an uploaded Northstar PDF and correctly surfaced a Gemini `API_KEY_INVALID` error without crashing, using a placeholder key)

---

## 4.4 Vector Retrieval

* [x] Implement workspace-scoped vector retrieval — `DocumentChunkRepository.search_by_embedding` (added in Increment 2, exercised here) + `application/retrieval/vector_search_service.py::VectorSearchService`, plain sequential scan over pgvector cosine distance (no ANN index yet — RAG_SYSTEM.md §18, acceptable at Northstar's corpus size)
* [x] Define candidate limit — `RETRIEVAL_CANDIDATE_LIMIT` setting (default 15, RAG_SYSTEM.md §19), passed as `limit` to `VectorSearchService.search`
* [x] Capture similarity score — `RetrievalResult.vector_score` (`1 - cosine_distance`, matching RAG_SYSTEM.md §26's `scores.vector` convention)
* [x] Add known-query tests — `tests/integration/test_vector_search_service.py`: ranking order with a controllable stub embedding provider, cross-workspace isolation, empty result when no chunks are embedded yet

---

## 4.5 Lexical Retrieval

* [x] Select PostgreSQL lexical search approach — built-in full-text search: generated `tsvector` column + GIN index + `websearch_to_tsquery`/`ts_rank` (ADR-028)
* [x] Record decision — ADR-028
* [x] Implement indexing — migration `f47b2e6a9c31` (`content_tsv GENERATED ALWAYS AS (to_tsvector('english', content)) STORED` + GIN index)
* [x] Implement workspace-scoped lexical retrieval — `DocumentChunkRepository.search_by_text`
* [x] Add tests — `tests/integration/test_document_chunk_repository.py`: keyword match + ranking, non-matching exclusion, workspace isolation

---

## 4.6 Hybrid Fusion

* [x] Implement candidate deduplication — `HybridSearchService` merges by stable `chunk_id` (RAG_SYSTEM.md §21)
* [x] Implement RRF or approved fusion strategy — Reciprocal Rank Fusion, k=60 (ADR-029), `application/retrieval/hybrid_search_service.py`
* [x] Preserve individual scores — `RetrievalScores` (`vector`/`lexical`/`fusion`/`rerank`, `application/retrieval/results.py`) matches RAG_SYSTEM.md §26's example schema
* [x] Add retrieval trace structure — every `RetrievalResult` carries all contributing scores together (which retriever(s) found it, at what score); full persisted observability logging of retrieval traces is Phase 9 scope (ARCHITECTURE.md §20), not part of Phase 4
* **Evaluation gate result (ADR-029): hybrid fusion does NOT clear RAG_SYSTEM.md §37's gate** — live comparison showed zero improvement over vector-only (Recall@5/Precision@5/MRR all identical, 1.00/0.20/1.00). Vector-only (`VectorSearchService`) remains the active default; `HybridSearchService`/`LexicalSearchService` exist, are tested, but are not wired into any default retrieval path.

---

## 4.7 Reranking

* [x] Select reranker — Gemini generation-based reranking (`gemini-2.5-flash`, structured JSON scoring), ADR-030
* [x] Record decision — ADR-030
* [x] Implement reranking interface — `infrastructure/rerankers/base.py::Reranker` protocol
* [x] Implement initial reranker — `infrastructure/rerankers/gemini_reranker.py::GeminiReranker` + `application/retrieval/reranking_service.py::RerankingService` (wraps any base search service)
* [x] Track latency/cost — per-call `duration_ms`/`prompt_token_count`/`candidates_token_count` logged (persisted observability is Phase 9 scope)
* [x] Add evaluation comparison — run live against real Gemini: **identical to vector-only on all three metrics** (Recall@5/Precision@5/MRR = 1.00/0.20/1.00, no change). Does not clear the RAG_SYSTEM.md §37 gate (ADR-030). Vector-only (no reranking) remains the active default. (Note: `RERANKER_MODEL` default was corrected from `gemini-2.5-flash`, retired for new users mid-increment, to the rolling alias `gemini-flash-latest`.)

---

## 4.8 Context Selection

* [x] Implement token-aware context selection — `application/retrieval/context_selection_service.py::ContextSelectionService`, `CONTEXT_TOKEN_BUDGET` setting (default 4000, RAG_SYSTEM.md §25 — deliberately well below typical model context windows)
* [x] Reduce duplicate evidence — word-overlap (Jaccard ≥0.8) redundancy check drops near-duplicate chunks against already-selected ones
* [x] Preserve source diversity — a side effect of redundancy avoidance (RAG_SYSTEM.md §24: "prefer evidence diversity when several chunks express the same information"), not a separate quota mechanism the docs didn't ask for
* [x] Return structured evidence — reuses `RetrievalResult` (already structured per RAG_SYSTEM.md §26); no new wrapper type needed
* Tests — `tests/unit/test_context_selection_service.py`: budget cutoff, always-keep-first-candidate, redundancy dropping, order preservation, empty input

---

## 4.9 RAG Citations

* [x] Generate stable evidence IDs — `DocumentChunk.id` (a UUID, already stable per DATA_MODEL.md §7) serves as the evidence ID directly; nothing new to mint
* [x] Include source metadata — already carried on every `RetrievalResult` (document title, page, section)
* [x] Validate evidence references — `application/retrieval/citation_service.py::CitationValidationService`: a cited `chunk_id` is valid only if present in the actual retrieved/workspace-scoped result set for that query, which simultaneously proves existence + workspace ownership + "was actually retrieved" (RAG_SYSTEM.md §28's three checks) in one lookup; unsupported IDs raise rather than silently drop (SECURITY.md §39, fail closed)
* [x] Add citation tests — `tests/unit/test_citation_service.py`: valid resolution, rejection of fabricated/foreign IDs, ordering, empty input
* Note: this validates citations against a given retrieval result set now; there is no agent yet (Phase 6) to actually produce cited claims, and no persisted `Evidence` table yet (Phase 8) — this closes the RAG-layer half of the citation contract that Phase 6/8 will call into.

---

## 4.10 Retrieval Evaluation

* [x] Create retrieval evaluation questions — already exists: the 5 `retrieval`-tagged entries in the canonical `data/northstar/eval/evaluation_questions.json` (DATASET.md §33, produced in Phase 2); no separate question set was created for this phase, per DATASET.md §33's "exactly one evaluation question file for the project"
* [x] Implement Recall@K — `scripts/evaluate_retrieval.py` (K=5)
* [x] Implement Precision@K — same script
* [x] Implement MRR — same script
* [x] Record vector baseline — run live against real Gemini: **Recall@5 = 1.00, Precision@5 = 0.20, MRR = 1.00** (ADR-027). Recall/MRR already at ceiling; Precision@5 is capped by the corpus containing only 5 total chunks, not by ranking quality.
* [x] Compare hybrid retrieval — run live against real Gemini: identical to the vector-only baseline on all three metrics (delta = +0.00). Does not clear the RAG_SYSTEM.md §37 gate (ADR-029). Vector-only remains the active default.
* [x] Compare reranking — run live against real Gemini: identical to vector-only/hybrid on all three metrics (delta = 0.00). Does not clear the RAG_SYSTEM.md §37 gate (ADR-030). Vector-only remains the active default.

**Phase 4 RAG retrieval pipeline: complete.** Vector-only retrieval (`VectorSearchService`) is the active default, per three separate live-measured gate results (ADR-027/029/030) all showing no headroom for lexical/fusion/reranking to improve on an already-at-ceiling baseline at Northstar's 5-document corpus size. All three alternative stages (lexical, hybrid, reranking) are implemented, tested, and available to revisit if the corpus grows.

---

# Phase 5 — Analytics Engine

## 5.1 Dataset Catalog

* [x] Expose dataset metadata to analytics layer — `application/analytics/catalog_service.py::DatasetCatalogService`, built dynamically per request from the requesting workspace's READY `Dataset` records only (ADR-017); display names/columns only, never physical identifiers
* [x] Represent dataset relationships — `application/analytics/known_relationships.py`, the exact four pairs documented in ANALYTICS_ENGINE.md §7/DATASET.md §31, resolved dynamically against whichever datasets actually exist in the workspace
* [x] Build bounded schema context — `DatasetCatalog.render()`/`_render_selected_datasets()` (sql_generation_service.py) inject only the datasets a given plan actually selected, not the whole catalog (ANALYTICS_ENGINE.md §6)

---

## 5.2 Analysis Intent

* [x] Define structured analytical intent schema — `application/analytics/schemas.py::AnalyticalIntent`/`AnalysisPlan` (Pydantic, ADR-011)
* [x] Define analysis-plan schema — same file, `AnalysisPlan.steps`
* [x] Implement model generation — new `LLMProvider` abstraction (ADR-031) + `GeminiLLMProvider`/`FakeLLMProvider`; `application/analytics/planning_service.py::AnalysisPlanningService`
* [x] Validate structured output — `generate_structured()` validates against the Pydantic model directly (google-genai `response_schema`), raising `LLMProviderError` on invalid output rather than returning unparsed prose

---

## 5.3 SQL Generation

* [x] Define SQL generation prompt — `application/analytics/sql_generation_service.py::SqlGenerationService`, display-names-only per ANALYTICS_ENGINE.md §5, explicit correction-prompt path for bounded retry
* [x] Generate SQL from approved schema context — same service; only the plan-selected datasets' schema is included
* [x] Keep generated SQL observable — `logger.info` per generation attempt in the orchestrator (`query_database_tool.py`); persisted/queryable observability remains Phase 9 scope (matches the pattern already established in Phase 4)
* Identifier resolution (display name -> physical identifier, ANALYTICS_ENGINE.md §5) — `infrastructure/analytics/sql_resolver.py::resolve_identifiers`, AST-based (sqlglot, ADR-032) rewrite of `Table`/`Column` nodes, scope-aware (CTEs, GROUP BY/ORDER BY aliases). A real bug was caught and fixed via a live end-to-end run (`scripts/evaluate_analytics.py`): an unaliased table renamed to its physical identifier left dangling `orders.col_1`-style qualifiers elsewhere in the query — fixed by re-adding an alias equal to the original display name when none was explicit (`tests/unit/test_sql_resolver.py::test_unaliased_table_gets_an_alias_back_so_column_qualifiers_still_resolve`)

---

## 5.4 SQL Validator

* [x] Select SQL parser — `sqlglot` (ADR-032; pure-Python, no native extension, sufficient Postgres-dialect coverage for single-statement/table/function-level checks)
* [x] Validate statement type — `infrastructure/analytics/sql_validator.py::validate_and_bound`: root must be `exp.Select` (covers both plain SELECT and WITH...SELECT)
* [x] Reject multiple statements — stacked `;`-separated statements rejected (`tests/unit/test_sql_validator.py::test_rejects_stacked_statements`)
* [x] Enforce schema allowlist (`analytics` only) — every table must be schema-qualified to `analytics`; `app`/unqualified references rejected
* [x] Build the table allowlist dynamically per request from the requesting workspace's Dataset records (ADR-017) — no static/hardcoded table list — `AnalyticsQueryService._generate_valid_sql` builds `allowed_tables` from the workspace's own `DatasetCatalog.entries` each call
* [x] Add cross-workspace test: query referencing another workspace's physical table must be rejected — `tests/integration/test_analytics_query_service.py::test_cross_workspace_physical_table_is_rejected_even_though_it_really_exists` (two real workspaces, two real physical tables, verified against real Postgres)
* [x] Reject mutation/DDL — DELETE/DROP/UPDATE/TRUNCATE/ALTER/CREATE/INSERT/GRANT all rejected by the root-statement-type check (`test_rejects_non_select_statements`)
* [x] Enforce result bounds — `LIMIT` injected if absent, capped if excessive, via AST rewrite (never trusts the LLM to have added one, SECURITY.md §14)
* [x] Add extensive security tests — `tests/unit/test_sql_validator.py` (21 cases) + forbidden-function denylist (`pg_sleep`, `dblink`, `pg_read_file`, etc.) + table-valued-function-as-table rejection

---

## 5.5 Read-Only Execution

* [x] Create restricted analytics DB role — Alembic migration `44472a1e3a0b`: `NOLOGIN` role `opspilot_analytics_ro`, `SELECT`-only on `analytics` (present + future tables via `ALTER DEFAULT PRIVILEGES`), no privileges on `app` (ADR-032 — no second DB credential/secret, membership granted to the app's own connecting role)
* [x] Execute validated SQL using restricted role — `infrastructure/analytics/query_executor.py::AnalyticsQueryExecutor`, `SET LOCAL ROLE` on a **dedicated** connection (never the ambient per-request session — see ADR-032's Rationale for why), always rolled back
* [x] Configure timeout — `SET LOCAL statement_timeout`; verified against real Postgres that a `pg_sleep`-based query is actually canceled (`tests/integration/test_analytics_query_executor.py::test_query_exceeding_timeout_raises_timeout_error`)
* [x] Bound results — `fetchmany(max_rows)` as a second, independent bound beneath the validator's injected `LIMIT`
* [x] Normalize query output — `Decimal` -> `float`, `datetime`/`date` -> ISO string (`_normalize_value`)
* Additional real-Postgres verification beyond the checklist: mutation attempts and `app` schema reads are rejected by the role itself even when called directly, bypassing the validator entirely (defense in depth) — `test_readonly_role_rejects_mutation_even_without_the_validator`, `test_readonly_role_cannot_read_the_app_schema`, `test_mutation_attempt_does_not_actually_delete_rows`

---

## 5.6 Analytics Tool

* [x] Implement query_database tool facade — `application/analytics/query_database_tool.py::AnalyticsQueryService`, composing catalog -> planning -> SQL generation -> resolution -> validation (bounded retry, `ANALYTICS_MAX_SQL_GENERATION_ATTEMPTS`) -> execution. No agent exists yet (Phase 6) to call it — directly callable/tested, the same pattern Phase 4 established for `EmbeddingGenerationService`. No HTTP debug endpoint was added (API.md §16's endpoint is described as "potential"; Phase 4 did not add its RAG equivalent either — consistent precedent)
* [x] Return structured results — `AnalyticsQueryResult` (status enum + `QueryResult` + evidence + optional interpretation)
* [x] Convert relevant results to evidence — `application/analytics/results.py::AnalyticsEvidence` (DATA_MODEL.md §17 query-evidence shape: dataset_ids, sql, bounded result) — not yet a persisted `Evidence` row (Phase 8), same status as `RetrievalResult` in the RAG layer
* [x] Handle empty/error states — `AnalyticsQueryStatus.{NO_DATASETS,NO_RELEVANT_DATASET,GENERATION_FAILED,EXECUTION_FAILED}`, returned structurally rather than raised (`tests/integration/test_analytics_query_service.py`)

---

## 5.7 Metrics

* [x] Implement deterministic percentage-change utility — `application/analytics/metrics.py::calculate_percentage_change` (absolute/relative/percentage-point, matching the documented 4%->5% example exactly)
* [x] Implement reusable rate calculation if justified — `calculate_refund_rate`, `calculate_average_delivery_time` (reused by evaluation and, later, the agent)
* [x] Implement revenue-impact components if justified — `calculate_revenue_impact` (exact observed + optional labeled estimate, ANALYTICS_ENGINE.md §24)
* [x] Add unit tests — `tests/unit/test_metrics.py` (13 cases) + `calculate_metric` dispatcher (the single agent-facing entry point per AGENT_SYSTEM.md §13) with unknown-type/invalid-argument handling

---

## 5.8 Charts

* [x] Define chart specification schema — `application/analytics/charts.py::ChartSpec`/`ChartSeries` (DATA_MODEL.md §23 shape)
* [x] Convert verified analytics results to charts — `build_chart_from_result()`, a pure transform from an already-executed `QueryResult`
* [ ] Render frontend charts — **deliberately deferred to Phase 7.** No Investigation Workspace page exists yet to host a chart (Phase 7), and Phase 4 did not build ahead of its own consumer either (no retrieval debug UI). Building chart-rendering UI now would be a disconnected component per ROADMAP.md §2 ("build vertically... prefer complete small workflows over large disconnected components").

---

## 5.9 Analytics Evaluation

* [x] Add known numerical questions — reuses the existing 7 `analytics`-tagged entries in the canonical `data/northstar/eval/evaluation_questions.json` (DATASET.md §33); no separate question set created
* [x] Compare results with ground truth — `scripts/evaluate_analytics.py`, run live against real Gemini + real Postgres: **all 7 questions executed successfully end-to-end** (no crashes, no security violations); **5/7 matched their `expected_value`** within tolerance (unit-normalized fraction-vs-percentage comparison). The 2 misses are genuine methodology differences the LLM's SQL made a different (still defensible) choice on — e.g. total refunded revenue summed all refund rows rather than only `status='completed'` ones — not pipeline defects; not fixed by hand-tuning the prompt toward this specific ground truth, per CLAUDE.md §24 ("no hardcoded investigation answers")
* [x] Test semantic equivalence rather than exact SQL text — the evaluation compares computed numeric output, never generated SQL text, to the expected value (TESTING.md §12)

**Phase 5 Analytics Engine: complete.** Catalog -> planning -> SQL generation -> identifier resolution -> AST validation -> read-only execution -> deterministic metrics -> evidence-shaped structured result, all directly callable/tested without an agent (Phase 6 wires it in). New: ADR-031 (Gemini `LLMProvider` for structured generation) and ADR-032 (sqlglot AST validation; `SET LOCAL ROLE` read-only execution). 228/228 backend tests pass (`make test-api`, full disposable-container migration cycle including the new role migration's upgrade/downgrade). Frontend chart rendering (5.8's last item) is the one item intentionally deferred to Phase 7, disclosed above rather than silently skipped.

---

# Phase 6 — Investigation Agent

## 6.1 Agent Schemas

* [ ] Define InvestigationPlan
* [ ] Define InvestigationStep schema
* [ ] Define Finding schema
* [ ] Define Recommendation schema
* [ ] Define agent state

---

## 6.2 Agent Prompt

* [ ] Define orchestrator system prompt
* [ ] Define evidence rules
* [ ] Define insufficient-data behavior
* [ ] Define tool-use policy
* [ ] Version prompt

---

## 6.3 Tools

* [ ] Register search_documents
* [ ] Register query_database
* [ ] Register calculate_metric
* [ ] Implement analyze_feedback if required
* [ ] Implement generate_chart if required
* [ ] Validate all tool schemas

---

## 6.4 Investigation Loop

* [ ] Create initial plan
* [ ] Execute current step
* [ ] Process tool results
* [ ] Store observations
* [ ] Store evidence
* [ ] Update hypotheses
* [ ] Adapt plan when required
* [ ] Evaluate stopping condition
* [ ] Synthesize result

---

## 6.5 Guardrails

* [ ] Configure max steps
* [ ] Configure max tool calls
* [ ] Configure max LLM calls
* [ ] Configure investigation timeout
* [ ] Handle loop-limit termination

---

## 6.6 Investigation Persistence

* [ ] Implement Investigation model
* [ ] Implement InvestigationStep
* [ ] Implement ToolExecution
* [ ] Implement Evidence
* [ ] Persist lifecycle state

---

## 6.7 Agent Evaluation

* [ ] Primary refund investigation
* [ ] July 11 investigation
* [ ] customer segment investigation
* [ ] provider performance investigation
* [ ] product refund investigation
* [ ] unsupported-question scenario
* [ ] contradictory-evidence scenario

---

# Phase 7 — Investigation Workspace

## 7.1 API

* [ ] Create investigation
* [ ] Get investigation
* [ ] List investigations
* [ ] Get steps
* [ ] Get evidence
* [ ] Get result
* [ ] Cancel investigation if supported

---

## 7.2 SSE

* [ ] Define event schema
* [ ] Implement SSE endpoint
* [ ] Stream investigation lifecycle events
* [ ] Handle completion
* [ ] Handle failure
* [ ] Add tests

---

## 7.3 Frontend

* [ ] Create Ask OpsPilot interface
* [ ] Create investigation progress UI
* [ ] Display plan
* [ ] Display step statuses
* [ ] Display final result
* [ ] Display recommendations
* [ ] Display charts
* [ ] Create investigation history

---

# Phase 8 — Evidence System

* [ ] Create evidence viewer
* [ ] Display document source
* [ ] Display page/chunk reference
* [ ] Display analytical evidence
* [ ] Display SQL safely
* [ ] Display bounded query result
* [ ] Link findings to evidence
* [ ] Validate cross-workspace evidence access

---

# Phase 9 — Observability

* [ ] Record LLM executions
* [ ] Record provider/model
* [ ] Record token usage
* [ ] Estimate model cost
* [ ] Record tool duration
* [ ] Record investigation duration
* [ ] Record retrieval traces
* [ ] Create execution-details view
* [ ] Create failure-debug view

---

# Phase 10 — Evaluation

* [ ] Build evaluation runner
* [ ] Load evaluation question set
* [ ] Run retrieval evaluation
* [ ] Run deterministic analytics checks
* [ ] Run full investigation evaluations
* [ ] Track latency
* [ ] Track cost
* [ ] Track groundedness
* [ ] Track citation correctness
* [ ] Save comparable evaluation reports

---

# Phase 11 — Demo Intelligence

## P2

* [ ] Investigation graph
* [ ] event/anomaly timeline
* [ ] evidence-derived confidence model
* [ ] suggested follow-up investigations

Only implement after P0/P1 functionality is reliable.

---

# Phase 12 — Portfolio Polish

* [ ] Final dashboard polish
* [ ] error-state polish
* [ ] responsive layout
* [ ] architecture diagram
* [ ] screenshots
* [ ] final README
* [ ] local setup instructions
* [ ] demo script
* [ ] 60–120 second demo video
* [ ] CV project description
* [ ] portfolio project description

---

# Backlog Working Rule

Before starting a backlog item:

1. read CLAUDE.md,
2. read relevant docs,
3. inspect current implementation,
4. produce a plan,
5. identify affected files,
6. identify tests,
7. implement after approval if requested,
8. verify,
9. update the checkbox only when actually done.

Do not check items merely because partial code exists.
