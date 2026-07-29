# OpsPilot — System Architecture

## 1. Architecture Goals

The architecture should optimize for:

* clarity,
* modularity,
* testability,
* traceability,
* AI experimentation,
* portfolio-quality engineering,
* local development simplicity.

The system should be sophisticated enough to demonstrate real engineering decisions without introducing unnecessary distributed-systems complexity.

---

# 2. Architecture Style

OpsPilot uses a:

## Modular Monolith

The application runs as a small number of deployable processes while maintaining explicit module boundaries internally.

We intentionally avoid microservices in V1.

Reasons:

* lower operational complexity,
* easier local development,
* easier debugging,
* easier refactoring,
* no current scaling requirement justifying distributed services,
* clearer learning experience.

Modules should nevertheless communicate through explicit interfaces where practical.

---

# 3. High-Level Architecture

```text
┌───────────────────────────────────────────┐
│                  User                     │
└──────────────────────┬────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────┐
│             Next.js Frontend              │
│                                           │
│ Dashboard                                 │
│ Data Sources                              │
│ Investigation Workspace                   │
│ Evidence Viewer                           │
│ Observability                             │
└──────────────────────┬────────────────────┘
                       │
                 HTTP / SSE
                       │
                       ▼
┌───────────────────────────────────────────┐
│               FastAPI API                 │
└──────────────────────┬────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────┐
│            Application Layer              │
│                                           │
│ Investigation Service                     │
│ Data Source Service                       │
│ Retrieval Service                         │
│ Analytics Service                         │
│ Agent Orchestrator                        │
│ Evidence Service                          │
│ Evaluation Service                        │
└──────────┬─────────────┬─────────────┬────┘
           │             │             │
           ▼             ▼             ▼
      PostgreSQL       Redis       LLM Providers
      + pgvector                    Embeddings
```

---

# 4. Runtime Components

## Web Application

Technology:

Next.js + TypeScript

Responsibilities:

* user interface,
* navigation,
* file uploads,
* investigation interaction,
* live investigation state,
* evidence presentation,
* analytical charts,
* observability presentation.

The frontend must not contain core business rules.

---

## API Application

Technology:

FastAPI

Responsibilities:

* HTTP API,
* request validation,
* authentication,
* authorization,
* application-service invocation,
* streaming investigation events,
* response serialization.

API handlers should remain thin.

---

## PostgreSQL

Primary durable datastore.

Used for:

* users,
* workspaces,
* documents,
* document metadata,
* document chunks,
* datasets,
* investigations,
* investigation steps,
* tool executions,
* evidence,
* application state,
* structured demo/business data.

---

## pgvector

Vector storage inside PostgreSQL.

Used for:

* document embeddings,
* semantic similarity search.

Reason for V1:

Keeps structured and vector infrastructure together and avoids adding a dedicated vector database before necessary.

---

## Redis

Potential responsibilities:

* caching,
* temporary execution state,
* background-job coordination,
* event delivery,
* rate limiting if later required.

Redis should not become the primary durable datastore.

---

## Background Worker

Long-running operations should eventually execute outside normal HTTP request lifecycles.

Potential jobs:

* PDF parsing,
* embedding generation,
* indexing,
* dataset processing,
* long investigations,
* evaluation runs.

The worker implementation must be documented through an architecture decision before adoption.

---

# 5. Backend Logical Layers

The backend should conceptually contain:

```text
API
 ↓
Application
 ↓
Domain
 ↓
Infrastructure
```

---

## API Layer

Responsibilities:

* HTTP routing
* authentication context
* validation
* status codes
* serialization

Should not:

* perform business analytics,
* directly query vector stores,
* orchestrate agents,
* contain SQL generation logic.

---

## Application Layer

Responsibilities:

* use cases,
* workflows,
* service coordination,
* transaction boundaries where appropriate.

Examples:

* CreateInvestigation
* UploadDocument
* ProcessDataset
* ExecuteInvestigation
* GetEvidence

---

## Domain Layer

Contains core business concepts and rules.

Potential concepts:

* Workspace
* DataSource
* Investigation
* InvestigationStep
* Evidence
* ToolExecution

Domain code should avoid unnecessary framework coupling.

---

## Infrastructure Layer

Contains implementations for external systems.

Examples:

* PostgreSQL repositories (SQLAlchemy ORM for application-domain entities, SQLAlchemy Core for dynamic analytics tables — ADR-020)
* pgvector retrieval
* Redis
* LLM providers
* embedding providers
* PDF parsers
* background-job system (technology deferred to Phase 3 — ADR-018)

---

# 6. Repository Structure (Approved V1 Structure)

This is the approved V1 repository structure (ADR-021), not a tentative suggestion:

```text
opspilot/
├── CLAUDE.md
├── README.md
├── docs/
├── apps/
│   ├── api/
│   │   └── app/
│   │       ├── api/            # HTTP routes, request/response schemas
│   │       ├── core/            # settings, env loading, logging, shared config
│   │       ├── domain/          # entities, value objects, domain rules
│   │       ├── application/     # use cases / services
│   │       └── infrastructure/  # DB repositories, LLM providers, parsers, external adapters
│   └── web/
├── scripts/
├── infra/
│   └── docker/
└── tests/
    ├── unit/
    ├── integration/
    ├── api/
    ├── e2e/
    └── evaluation/
```

Backend application code lives under `apps/api/app/`, organized by logical layer — matching the API → Application → Domain → Infrastructure layering in §5 above — rather than by business module:

* `api/` — HTTP layer responsibilities from §5.1 (routing, validation, auth context, serialization)
* `core/` — settings, environment loading, structured logging baseline
* `domain/` — entities and rules (Workspace, DataSource, Investigation, Evidence, ...)
* `application/` — use cases (CreateInvestigation, UploadDocument, ProcessDataset, ExecuteInvestigation, GetEvidence)
* `infrastructure/` — PostgreSQL repositories (ADR-020), pgvector retrieval, Redis, LLM/embedding providers, PDF parsers

Business modules (ingestion, retrieval, analytics, agents, investigations, evidence, evaluation, observability) are organized as subpackages *within* `domain/`, `application/`, and `infrastructure/`. There is no separate top-level `services/*` tree — that earlier sketch is superseded by ADR-021, since it duplicated the layering already expressed inside `apps/api/app/`.

Frontend application code lives under `apps/web/`.

Do not create empty placeholder subpackages for a business module before it has real code — create each subpackage when its first real file is added, not upfront.

---

# 7. Core Modules

## Ingestion Module

Responsibilities:

* receive uploaded data,
* identify file type,
* validate uploads,
* parse supported formats,
* extract metadata,
* normalize data,
* persist records,
* trigger indexing.

Initial formats:

* PDF
* CSV
* Markdown
* plain text

---

## Retrieval Module

Responsibilities:

* query processing,
* semantic retrieval,
* keyword retrieval,
* hybrid result fusion,
* reranking,
* context selection,
* source metadata preservation.

Target architecture:

```text
Query
 ↓
Query Processing
 ↓
┌───────────────┬─────────────────┐
│ Vector Search │ Keyword Search  │
└───────┬───────┴────────┬────────┘
        └────────┬────────┘
                 ↓
              Fusion
                 ↓
              Rerank
                 ↓
         Context Selection
```

Implementation details will be defined in RAG_SYSTEM.md.

---

# 8. Analytics Module

Responsibilities:

* inspect structured dataset schemas,
* understand available tables/columns,
* translate analytical intent into controlled queries,
* validate generated SQL,
* execute read-only SQL,
* compute metrics,
* generate structured analytical outputs,
* generate chart specifications/data.

Target workflow:

```text
Question
 ↓
Dataset Selection
 ↓
Schema Context
 ↓
Analysis Plan
 ↓
SQL Generation
 ↓
SQL Validation
 ↓
Read-Only Execution
 ↓
Result Validation
 ↓
Interpretation
```

LLMs must not directly access database connections.

---

# 9. Agent Module

V1 uses a single orchestrator.

Responsibilities:

* interpret business question,
* determine investigation strategy,
* create investigation steps,
* select tools,
* evaluate tool results,
* form hypotheses,
* determine whether more evidence is required,
* synthesize conclusions,
* propose recommendations.

Agent tools expose controlled capabilities.

Initial candidates:

```text
search_documents
query_database
calculate_metric
analyze_feedback
generate_chart
```

Detailed contracts belong in AGENT_SYSTEM.md.

---

# 10. Investigation Module

Investigation is the central workflow abstraction.

An investigation represents:

* user question,
* plan,
* execution progress,
* tool calls,
* evidence,
* findings,
* final explanation,
* recommendations.

Example lifecycle:

```text
CREATED
   ↓
PLANNING
   ↓
RUNNING
   ↓
SYNTHESIZING
   ↓
COMPLETED
```

Possible failure states:

```text
FAILED
CANCELLED
```

Each meaningful step should be persisted.

---

# 11. Evidence Module

Evidence connects conclusions to underlying information.

Evidence types may include:

* document evidence,
* query evidence,
* metric evidence,
* analytical evidence.

Conceptually:

```text
Claim
 ↓
Evidence Reference
 ↓
Underlying Source
```

Evidence should retain enough metadata for UI inspection.

Examples:

Document:

* document ID
* page
* chunk
* text span

Structured data:

* query
* columns
* aggregation
* source dataset

---

# 12. AI Provider Architecture

Use explicit provider abstractions.

Conceptually:

```text
LLMProvider

generate()
generate_structured()
stream()
```

Potential implementations:

```text
OpenAIProvider
AnthropicProvider
GoogleProvider
```

Embedding providers should similarly avoid unnecessary coupling.

Exact interfaces should remain minimal and driven by real use cases.

---

# 13. Structured AI Outputs

Where AI outputs control application behavior, prefer structured schemas.

Examples:

* InvestigationPlan
* ToolRequest
* QueryIntent
* Finding
* Recommendation

Avoid parsing unconstrained prose when the application requires machine-readable state.

---

# 14. Streaming / Live Progress

Investigation execution should be visible in the UI.

Preferred initial direction:

Server-Sent Events (SSE)

rather than WebSockets unless bidirectional real-time communication becomes necessary.

Reason:

Investigation progress is primarily server → client.

Possible events:

```text
investigation.started
plan.created
step.started
tool.started
tool.completed
evidence.added
step.completed
investigation.completed
investigation.failed
```

This decision should be revisited if requirements change.

---

# 15. Data Flow — Document Upload

```text
User Upload
 ↓
API
 ↓
Validation
 ↓
Document Record
 ↓
Parser
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embedding
 ↓
PostgreSQL + pgvector
 ↓
READY
```

Large processing operations may move to a worker.

---

# 16. Data Flow — CSV Upload

```text
CSV Upload
 ↓
Validation
 ↓
Schema Detection
 ↓
Dataset Metadata
 ↓
Structured Storage
 ↓
Profile / Statistics
 ↓
READY
```

Exact storage strategy for uploaded business datasets will be defined during the data-model phase.

---

# 17. Data Flow — Investigation

```text
User Question
 ↓
Create Investigation
 ↓
Agent Planning
 ↓
Tool Selection
 ↓
┌──────────────┬──────────────┐
│ Retrieval    │ Analytics    │
└──────┬───────┴───────┬──────┘
       │               │
       └───────┬───────┘
               ↓
         Evidence Store
               ↓
         Agent Reasoning
               ↓
          More Tools?
           /       \
         Yes       No
          │         │
          └────┐    ↓
               │ Synthesis
               │    ↓
               └ Recommendation
                    ↓
                 Complete
```

---

# 18. Database Access Boundaries

The application database and AI-generated analytics access should be conceptually separated.

AI-generated SQL must execute through a restricted analytics interface.

The LLM must never receive:

* raw database credentials,
* unrestricted ORM sessions,
* general-purpose database tools.

Prefer dedicated read-only database roles for analytical execution.

---

# 19. Security Boundaries

Trust levels:

## Trusted

* application code
* system-level agent rules
* validated application configuration

## Untrusted

* user prompts
* uploaded PDFs
* uploaded text
* CSV contents
* generated LLM output
* generated SQL before validation

Uploaded documents may contain prompt injection attempts.

Document content must be treated as data, not system instructions.

---

# 20. Observability Architecture

Important workflows should create structured traces.

Conceptual hierarchy:

```text
Investigation
 ├── Step
 │    ├── Tool Execution
 │    └── Evidence
 │
 └── LLM Execution
```

Captured metadata may include:

* timestamp,
* duration,
* model,
* input token count,
* output token count,
* estimated cost,
* error,
* retrieval results,
* reranking scores.

Sensitive data should not be logged unnecessarily.

---

# 21. Error Handling

Errors should be classified.

Examples:

* ValidationError
* DataSourceProcessingError
* RetrievalError
* AnalyticsQueryError
* ToolExecutionError
* LLMProviderError
* InvestigationFailedError

Failures should not automatically destroy investigation history.

When possible, preserve partial traces for debugging.

---

# 22. Retry Philosophy

Retry only operations where retrying is safe.

Candidates:

* transient LLM provider failure,
* temporary embedding API failure,
* transient worker/network issue.

Do not blindly retry:

* side-effecting tools,
* invalid SQL,
* deterministic validation failures.

Use bounded retries.

---

# 23. Evaluation Architecture

Evaluation should operate separately from normal user investigations.

Evaluation datasets may include:

* known questions,
* expected evidence,
* expected numerical outputs,
* expected conclusions.

Retrieval metrics may include:

* Recall@K
* Precision@K
* MRR

Generation/evidence evaluation may include:

* groundedness
* citation correctness
* answer relevance

Exact methodology belongs in TESTING.md / evaluation documentation.

---

# 24. Scaling Philosophy

V1 should optimize for correctness and architecture quality, not hypothetical massive scale.

Do not introduce infrastructure for millions of users without measured need.

Potential future scaling boundaries include:

* workers,
* document processing,
* retrieval,
* analytical query execution.

The modular architecture should allow extraction of components later if necessary.

---

# 25. Architectural Constraints

The following require explicit discussion before introduction:

* microservices
* Kubernetes
* Kafka
* dedicated vector databases
* multiple autonomous agents
* arbitrary Python execution
* write-enabled AI database access
* external action tools
* new persistent infrastructure

Complexity must earn its place.

---

# 26. Architecture Decision Process

Significant changes should be recorded in DECISIONS.md.

The registry there is authoritative; do not restate ADR numbers elsewhere, since duplicated numbering drifts out of sync as new ADRs are added. As of this writing it includes decisions such as:

* ADR-001 — Modular Monolith
* ADR-003 — PostgreSQL as Primary Database
* ADR-004 — pgvector for Vector Storage
* ADR-006 — One Orchestrator Agent for V1
* ADR-010 — SSE for Investigation Progress
* ADR-017 — Per-Dataset Generated Analytics Tables With Dynamic Workspace-Scoped SQL Allowlist
* ADR-018 — Defer Background Worker Technology Selection to Phase 3
* ADR-019 — V1 Authentication Strategy
* ADR-020 — Database Access Strategy: SQLAlchemy 2.x + Alembic
* ADR-021 — Finalized V1 Repository Layout

See DECISIONS.md for the full, current list.

Each decision should describe:

* context,
* decision,
* rationale,
* alternatives,
* consequences.
