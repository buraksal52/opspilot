# OpsPilot — Development Roadmap

## 1. Roadmap Purpose

This roadmap defines the implementation order for OpsPilot.

The project should be developed incrementally.

Each phase must produce a working, testable improvement to the system.

Do not begin later phases simply because they appear interesting.

Prioritize:

1. correctness,
2. clear architecture,
3. testability,
4. product value,
5. demo quality.

The project should remain runnable throughout development.

---

# 2. Development Principles

## Build vertically

Prefer complete small workflows over large disconnected components.

Example:

Bad:

* build all database models,
* then all APIs,
* then all AI services,
* then frontend.

Better:

* build one complete data upload flow,
* verify it,
* then expand.

---

## Avoid premature complexity

Do not introduce:

* microservices,
* Kubernetes,
* Kafka,
* multi-agent systems,
* dedicated vector databases,
* complex event infrastructure

unless later requirements justify them.

---

## Every phase has a Definition of Done

A phase is not complete because code exists.

It is complete only when:

* core functionality works,
* tests exist where appropriate,
* known critical bugs are resolved,
* relevant documentation is updated,
* functionality has been verified.

---

# 3. Phase Overview

```text
Phase 0 — Product & Architecture
Phase 1 — Project Foundation
Phase 2 — Northstar Dataset
Phase 3 — Data Ingestion
Phase 4 — Retrieval / RAG
Phase 5 — Structured Analytics
Phase 6 — Investigation Agent
Phase 7 — Investigation Workspace
Phase 8 — Evidence System
Phase 9 — Observability
Phase 10 — Evaluation
Phase 11 — Demo Intelligence
Phase 12 — Polish & Portfolio
```

---

# 4. Phase 0 — Product & Architecture

## Goal

Define the product and technical boundaries before implementation.

## Required Documents

* CLAUDE.md
* docs/PRODUCT.md
* docs/ARCHITECTURE.md
* docs/ROADMAP.md
* docs/DATA_MODEL.md
* docs/DATASET.md

Later documents:

* docs/RAG_SYSTEM.md
* docs/AGENT_SYSTEM.md
* docs/ANALYTICS_ENGINE.md
* docs/API.md
* docs/TESTING.md
* docs/SECURITY.md
* docs/DECISIONS.md

## Definition of Done

* product scope is clear,
* V1 boundaries are explicit,
* core architecture is documented,
* development phases are defined,
* initial data model exists,
* Northstar Commerce demo scenario is defined.

---

# 5. Phase 1 — Project Foundation

## Goal

Create a stable local development environment and application skeleton.

## Backend

Create:

* FastAPI application,
* configuration system,
* environment variable management,
* database connection,
* migrations,
* health endpoint,
* structured logging baseline,
* basic error handling.

## Frontend

Create:

* Next.js application,
* TypeScript configuration,
* Tailwind,
* shadcn/ui setup,
* dashboard shell,
* navigation.

## Infrastructure

Docker Compose should include:

* API,
* web,
* PostgreSQL,
* Redis.

## Initial Domain Models

Implement only foundational entities required by Phase 1:

* User,
* Workspace.

Authentication may remain minimal for the portfolio/demo version.

## Definition of Done

Running:

```bash
docker compose up
```

should start the required development services.

The frontend must be able to call the backend health endpoint.

Database migrations must run successfully.

---

# 6. Phase 2 — Northstar Commerce Dataset

## Goal

Create the controlled synthetic business environment used to develop and evaluate OpsPilot.

## Deliverables

Generate:

* customers
* products
* orders
* refunds
* support tickets

Create business documents:

* Refund Policy
* Shipping Policy
* Customer Support Handbook
* Shipping Provider Migration Report
* Incident Report

## Important Requirement

The dataset must contain causal and correlated patterns intentionally designed for investigation.

The primary hidden event:

July 11 shipping provider migration.

Expected measurable consequences:

* delivery times increase,
* shipping-related tickets increase,
* refunds increase,
* customer satisfaction decreases,
* repeat purchases decline among affected customers.

## Definition of Done

The hidden business story must be independently verifiable using deterministic analysis.

OpsPilot conclusions must not rely on hardcoded answers.

---

# 7. Phase 3 — Data Ingestion

## Goal

Allow OpsPilot to ingest and manage structured and unstructured data.

## 3.1 Data Source Management

Implement:

* data source records,
* processing status,
* source metadata,
* upload lifecycle.

Possible statuses:

```text
UPLOADED
PROCESSING
READY
FAILED
```

## 3.2 Document Upload

Support:

* PDF
* Markdown
* plain text

Pipeline:

```text
Upload
→ Validation
→ Parsing
→ Text extraction
→ Metadata extraction
→ Persistence
```

Do not generate embeddings yet unless required by the implementation flow.

## 3.3 CSV Upload

Support:

* CSV validation,
* schema inference,
* row counts,
* column metadata,
* basic data profiling,
* structured storage.

## 3.4 Frontend

Create Data Sources interface.

Users should be able to:

* upload files,
* see processing state,
* inspect metadata,
* delete sources.

## Definition of Done

Northstar structured and unstructured data can be loaded into OpsPilot through real ingestion flows.

---

# 8. Phase 4 — Retrieval / RAG

## Goal

Build reliable retrieval over internal documents.

## 4.1 Chunking

Implement:

* document chunk creation,
* source metadata preservation,
* configurable chunking strategy.

## 4.2 Embeddings

Implement:

* embedding provider abstraction,
* embedding generation,
* pgvector persistence.

## 4.3 Vector Retrieval

Implement semantic similarity search.

## 4.4 Keyword Retrieval

Add keyword-based retrieval.

Potential approaches should be evaluated before implementation.

## 4.5 Hybrid Search

Combine vector and lexical results using a documented fusion strategy.

## 4.6 Reranking

Add reranking after initial retrieval.

## 4.7 Context Selection

Select final context passed to the model.

## 4.8 Citation Mapping

Preserve source references through the entire pipeline.

## Definition of Done

Queries about Northstar business documents return relevant passages and correct source metadata.

Retrieval behavior must be testable.

---

# 9. Phase 5 — Structured Analytics

## Goal

Allow natural-language business questions to produce safe, deterministic analysis over structured data.

## 5.1 Dataset Catalog

The system should understand:

* available datasets,
* tables,
* columns,
* data types,
* important relationships.

## 5.2 Analysis Planning

Translate business questions into structured analytical intent.

Example:

Question:

> Did refund rates increase after July 11?

Plan:

* identify orders before and after July 11,
* calculate refund rate for both periods,
* compare results.

## 5.3 SQL Generation

Generate analytical SQL from controlled context.

## 5.4 SQL Validation

Before execution enforce:

* read-only queries,
* allowed tables,
* row limits,
* timeouts,
* syntax validation.

## 5.5 Query Execution

Execute against read-only analytics access.

## 5.6 Result Interpretation

LLM may explain results only after deterministic computation.

## 5.7 Chart Data

Allow analytical results to be transformed into chart-ready structured data.

## Definition of Done

OpsPilot can correctly answer deterministic analytical questions such as:

* refund rate before vs after July 11,
* delivery time trends,
* ticket counts by category,
* refund rate by product,
* affected customer segments.

---

# 10. Phase 6 — Investigation Agent

## Goal

Combine retrieval and analytics into a controlled investigation workflow.

## Architecture

Use:

One orchestrator agent + explicit tools.

Initial tools may include:

* search_documents
* query_database
* calculate_metric
* analyze_feedback
* generate_chart

## 6.1 Investigation Planning

The agent should produce a structured plan.

## 6.2 Tool Selection

The agent selects tools based on the current investigation state.

## 6.3 Observation Loop

Tool results should update investigation state.

## 6.4 Evidence Collection

Evidence must be collected during investigation.

## 6.5 Synthesis

The final answer should include:

* findings,
* explanation,
* evidence,
* recommendations.

## Definition of Done

The agent can perform the primary Northstar investigation:

> Why did refunds increase this month?

without a hardcoded workflow or answer.

---

# 11. Phase 7 — Investigation Workspace

## Goal

Create the primary user-facing workflow.

## Features

Users should be able to:

* ask a business question,
* start an investigation,
* see progress,
* inspect steps,
* inspect tool activity,
* read the final report,
* reopen past investigations.

## Live Progress

Prefer SSE unless requirements later justify WebSockets.

Possible UI states:

```text
Planning investigation...
Analyzing refund trends...
Searching support tickets...
Reviewing internal documents...
Calculating revenue impact...
Generating conclusions...
```

## Definition of Done

The full investigation can be demonstrated visually from question to result.

---

# 12. Phase 8 — Evidence System

## Goal

Make important conclusions inspectable.

## Evidence Types

Support:

* document evidence,
* SQL/query evidence,
* calculated metric evidence.

## UI

Users should be able to select a claim and inspect supporting evidence.

Example:

```text
Claim:
Refund requests increased 26%.

Evidence:
refund analysis query
Jul 1–10 vs Jul 11–20
```

## Definition of Done

Important findings in the main demo have inspectable evidence.

---

# 13. Phase 9 — Observability

## Goal

Make AI execution understandable and debuggable.

## Capture

* investigation duration,
* step duration,
* LLM calls,
* model names,
* token usage,
* estimated cost,
* tool calls,
* tool failures,
* retrieved chunks,
* retrieval scores,
* reranker scores.

## UI

Create an execution details view.

Observability should prioritize engineering usefulness over decorative complexity.

## Definition of Done

A failed or poor-quality investigation can be debugged using stored execution information.

---

# 14. Phase 10 — Evaluation

## Goal

Measure whether OpsPilot actually works.

## Retrieval Evaluation

Possible metrics:

* Recall@K
* Precision@K
* MRR

## Investigation Evaluation

Evaluate:

* numerical correctness,
* evidence correctness,
* citation correctness,
* groundedness,
* answer relevance.

## Evaluation Dataset

Create known Northstar questions and expected outputs.

Example categories:

* factual document retrieval,
* numerical analytics,
* multi-source investigation,
* causal hypothesis requiring multiple signals.

## Definition of Done

Core demo workflows have repeatable quality measurements.

---

# 15. Phase 11 — Demo Intelligence

## Goal

Add high-value portfolio differentiators only after the core system is reliable.

## P2 Features

### Investigation Graph

Visualize:

```text
Question
→ Plan
→ Tools
→ Evidence
→ Findings
```

### Event Timeline

Identify important business events and downstream metric changes.

### Confidence Model

Provide confidence based on measurable signals such as:

* evidence coverage,
* agreement between sources,
* retrieval quality,
* analytical support.

Do not use arbitrary LLM self-confidence scores.

### Suggested Investigations

Generate useful follow-up questions.

## Definition of Done

At least one visually strong demo experience exists without compromising correctness.

---

# 16. Phase 12 — Polish & Portfolio

## Goal

Prepare OpsPilot as a professional portfolio project.

## Required

* stable demo dataset,
* polished primary investigation,
* responsive UI,
* error states,
* loading states,
* README,
* architecture diagram,
* screenshots,
* short demo video,
* setup instructions.

## README should include

* problem,
* solution,
* architecture,
* core capabilities,
* AI engineering decisions,
* security considerations,
* evaluation,
* screenshots,
* demo scenario.

## Definition of Done

A technical reviewer should be able to understand:

* what OpsPilot does,
* how it works,
* why architectural choices were made,
* what AI components are actually doing.

---

# 17. Priority Model

## P0 — Core Product

* ingestion
* structured analytics
* retrieval
* investigation agent
* evidence
* investigation UI

## P1 — Engineering Quality

* hybrid retrieval
* reranking
* background processing
* observability
* evaluation
* robust tests

## P2 — Portfolio Differentiators

* investigation graph
* anomaly/event timeline
* confidence model
* suggested investigations

## P3 — Future Product

* external integrations
* scheduled investigations
* collaboration
* notifications
* action execution
* external operational tools

---

# 18. Scope Control Rule

Before adding any feature, ask:

1. Does it improve the core investigation loop?
2. Does it teach or demonstrate an important engineering capability?
3. Does it improve reliability?
4. Does it improve the portfolio demo meaningfully?

If the answer to all four is no, defer the feature.
