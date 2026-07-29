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

* [ ] Create deterministic generation package/script
* [ ] Define fixed random seed
* [ ] Define generator configuration
* [ ] Add output directory structure

---

## 2.2 Customers

* [ ] Generate customer IDs
* [ ] Generate customer segments
* [ ] Generate acquisition channels
* [ ] Generate geographic attributes
* [ ] Generate derived lifetime metrics where appropriate

---

## 2.3 Products

* [ ] Generate product catalog
* [ ] Generate categories
* [ ] Generate pricing
* [ ] Generate costs
* [ ] Validate product IDs

---

## 2.4 Orders

* [ ] Generate June–July order timeline
* [ ] Generate customer/product relationships
* [ ] Model SwiftShip baseline
* [ ] Introduce July 11 RapidShip migration
* [ ] Generate delivery-time distributions
* [ ] Generate delays
* [ ] Generate order values
* [ ] Generate statuses

---

## 2.5 Refunds

* [ ] Generate baseline refund behavior
* [ ] Increase late-delivery refund probability after incident
* [ ] Preserve unrelated refund reasons
* [ ] Generate refund amounts
* [ ] Maintain order/customer relationships

---

## 2.6 Support Tickets

* [ ] Generate baseline ticket volume
* [ ] Generate ticket categories
* [ ] Generate realistic ticket text variation
* [ ] Increase shipping complaints after incident
* [ ] Generate sentiment
* [ ] Generate resolution time

---

## 2.7 Business Documents

* [ ] Create Refund Policy
* [ ] Create Shipping Policy
* [ ] Create Customer Support Handbook
* [ ] Create Shipping Provider Migration Report
* [ ] Create July Operations Incident Report

---

## 2.8 Ground Truth

* [ ] Generate private ground_truth.json
* [ ] Record incident date
* [ ] Record expected patterns
* [ ] Ensure runtime application never reads this as evidence

---

## 2.9 Validation

* [ ] Validate dataset relationships
* [ ] Validate provider migration timing
* [ ] Validate delivery-time increase
* [ ] Validate ticket increase
* [ ] Validate refund increase
* [ ] Validate realistic noise
* [ ] Produce validation summary

---

# Phase 3 — Data Ingestion

## 3.0 Background Worker Decision (supersedes ADR-018)

* [ ] Evaluate background worker technology options against actual Phase 3/4 workloads (PDF parsing, embedding generation)
* [ ] Record the decision as a new ADR that supersedes ADR-018
* [ ] Confirm Phase 1/2 work does not implicitly depend on a specific worker implementation

---

## 3.1 DataSource Domain

* [ ] Implement DataSource model
* [ ] Implement status enum
* [ ] Add migration
* [ ] Add application service
* [ ] Add tests

---

## 3.2 Upload API

* [ ] Implement multipart upload endpoint
* [ ] Validate file size
* [ ] Validate MIME/file format
* [ ] Sanitize handling of filenames
* [ ] Persist DataSource
* [ ] Handle failures

---

## 3.3 Document Ingestion

* [ ] Implement Document model
* [ ] Implement PDF parser
* [ ] Implement Markdown parser
* [ ] Implement plain-text parser
* [ ] Normalize extracted text
* [ ] Preserve source metadata
* [ ] Add parser tests

---

## 3.4 Dataset Ingestion

* [ ] Implement Dataset model (per ADR-017: `physical_table_name` generated by the application, distinct from user-facing `name`)
* [ ] Parse CSV safely
* [ ] Infer column types
* [ ] Generate sanitized physical column identifiers (never derived directly from CSV header text)
* [ ] Create per-Dataset analytics table under `analytics.*` using only generated physical identifiers
* [ ] Insert rows
* [ ] Generate schema_definition with both `display_name` and `physical_name` per column
* [ ] Generate basic profile statistics
* [ ] Add ingestion tests, including tests for malicious/SQL-metacharacter column headers

---

## 3.5 Data Source UI

* [ ] Create Data Sources page
* [ ] Add upload interface
* [ ] Show processing states
* [ ] Show source metadata
* [ ] Add delete flow

---

# Phase 4 — RAG

## 4.1 DocumentChunk

* [ ] Implement DocumentChunk model
* [ ] Add pgvector extension
* [ ] Add vector column
* [ ] Add migration

---

## 4.2 Chunking

* [ ] Implement baseline chunking strategy
* [ ] Preserve page metadata
* [ ] Preserve section metadata where available
* [ ] Track token counts
* [ ] Add deterministic chunking tests

---

## 4.3 Embeddings

* [ ] Define EmbeddingProvider interface
* [ ] Implement initial provider
* [ ] Implement batch embedding
* [ ] Store embedding model metadata
* [ ] Handle failures
* [ ] Add tests

---

## 4.4 Vector Retrieval

* [ ] Implement workspace-scoped vector retrieval
* [ ] Define candidate limit
* [ ] Capture similarity score
* [ ] Add known-query tests

---

## 4.5 Lexical Retrieval

* [ ] Select PostgreSQL lexical search approach
* [ ] Record decision
* [ ] Implement indexing
* [ ] Implement workspace-scoped lexical retrieval
* [ ] Add tests

---

## 4.6 Hybrid Fusion

* [ ] Implement candidate deduplication
* [ ] Implement RRF or approved fusion strategy
* [ ] Preserve individual scores
* [ ] Add retrieval trace structure

---

## 4.7 Reranking

* [ ] Select reranker
* [ ] Record decision
* [ ] Implement reranking interface
* [ ] Implement initial reranker
* [ ] Track latency/cost
* [ ] Add evaluation comparison

---

## 4.8 Context Selection

* [ ] Implement token-aware context selection
* [ ] Reduce duplicate evidence
* [ ] Preserve source diversity
* [ ] Return structured evidence

---

## 4.9 RAG Citations

* [ ] Generate stable evidence IDs
* [ ] Include source metadata
* [ ] Validate evidence references
* [ ] Add citation tests

---

## 4.10 Retrieval Evaluation

* [ ] Create retrieval evaluation questions
* [ ] Implement Recall@K
* [ ] Implement Precision@K
* [ ] Implement MRR
* [ ] Record vector baseline
* [ ] Compare hybrid retrieval
* [ ] Compare reranking

---

# Phase 5 — Analytics Engine

## 5.1 Dataset Catalog

* [ ] Expose dataset metadata to analytics layer
* [ ] Represent dataset relationships
* [ ] Build bounded schema context

---

## 5.2 Analysis Intent

* [ ] Define structured analytical intent schema
* [ ] Define analysis-plan schema
* [ ] Implement model generation
* [ ] Validate structured output

---

## 5.3 SQL Generation

* [ ] Define SQL generation prompt
* [ ] Generate SQL from approved schema context
* [ ] Keep generated SQL observable

---

## 5.4 SQL Validator

* [ ] Select SQL parser
* [ ] Validate statement type
* [ ] Reject multiple statements
* [ ] Enforce schema allowlist (`analytics` only)
* [ ] Build the table allowlist dynamically per request from the requesting workspace's Dataset records (ADR-017) — no static/hardcoded table list
* [ ] Add cross-workspace test: query referencing another workspace's physical table must be rejected
* [ ] Reject mutation/DDL
* [ ] Enforce result bounds
* [ ] Add extensive security tests

---

## 5.5 Read-Only Execution

* [ ] Create restricted analytics DB role
* [ ] Execute validated SQL using restricted role
* [ ] Configure timeout
* [ ] Bound results
* [ ] Normalize query output

---

## 5.6 Analytics Tool

* [ ] Implement query_database tool facade
* [ ] Return structured results
* [ ] Convert relevant results to evidence
* [ ] Handle empty/error states

---

## 5.7 Metrics

* [ ] Implement deterministic percentage-change utility
* [ ] Implement reusable rate calculation if justified
* [ ] Implement revenue-impact components if justified
* [ ] Add unit tests

---

## 5.8 Charts

* [ ] Define chart specification schema
* [ ] Convert verified analytics results to charts
* [ ] Render frontend charts

---

## 5.9 Analytics Evaluation

* [ ] Add known numerical questions
* [ ] Compare results with ground truth
* [ ] Test semantic equivalence rather than exact SQL text

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
