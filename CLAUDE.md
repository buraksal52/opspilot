# OpsPilot — Claude Code Project Instructions

## 1. Project Overview

OpsPilot is an AI-native Business Intelligence and Operations platform.

Its purpose is to help users investigate business questions using structured and unstructured company data.

OpsPilot should not behave like a generic chatbot.

It should:

1. understand a business question,
2. create an investigation plan,
3. select the appropriate tools,
4. retrieve relevant documents,
5. analyze structured data,
6. collect evidence,
7. generate grounded conclusions,
8. recommend actions,
9. optionally execute explicitly permitted actions.

Example:

> Why did refunds increase this month?

OpsPilot should investigate relevant business data and documents instead of answering from general LLM knowledge.

---

# 2. Core Product Principle

The central product loop is:

Business Question
→ Investigation Plan
→ Tool Execution
→ Evidence Collection
→ Analysis
→ Explanation
→ Recommendation

All major architectural decisions should support this loop.

---

# 3. Current Product Scope

The initial version focuses on:

* CSV ingestion
* PDF ingestion
* structured business data analysis
* document retrieval
* hybrid RAG
* reranking
* evidence-backed answers
* AI tool calling
* investigation workflows
* execution tracing
* AI observability
* evaluation
* charts and analytical outputs

The first version does NOT require:

* Slack integration
* Gmail integration
* Google Drive integration
* Shopify integration
* Stripe integration
* mobile applications
* Kubernetes
* microservices
* enterprise SSO
* billing
* complex multi-agent swarms

Do not introduce these features unless explicitly requested.

---

# 4. Architecture Philosophy

Use a modular monolith.

Do not introduce microservices unless there is a demonstrated technical need.

The system should have clear module boundaries while remaining easy to develop and run locally.

Primary modules:

* ingestion
* retrieval
* analytics
* agents
* investigations
* evidence
* evaluation
* observability

Business logic must not live inside API route handlers.

API routes should handle:

* HTTP concerns
* input validation
* authentication
* serialization
* calling application services

Business logic belongs in application/domain services.

Infrastructure-specific implementations must be isolated where practical.

---

# 5. Technology Stack

## Frontend

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

## Backend

* Python
* FastAPI

## Database

* PostgreSQL

## Vector Storage

* PostgreSQL + pgvector

## Cache / Coordination

* Redis

## Background Processing

Use a background worker architecture where long-running operations require it.

The exact worker framework should be chosen deliberately and documented in DECISIONS.md.

## Development Environment

* Docker
* Docker Compose

---

# 6. AI Engineering Principles

AI components must be treated as probabilistic system components.

Never assume an LLM response is correct merely because it parses successfully.

Prefer:

* typed inputs
* typed outputs
* deterministic validation
* explicit tool contracts
* evidence tracking
* evaluation
* retries where safe
* bounded execution

Avoid:

* unrestricted agent autonomy
* implicit side effects
* hidden tool execution
* direct database access by LLMs
* arbitrary generated code execution

---

# 7. LLM Provider Abstraction

Business logic must not depend directly on a single LLM vendor.

Use an abstraction such as:

LLMProvider

Provider-specific implementations may include:

* OpenAI
* Anthropic
* Google

Switching providers should not require rewriting core business logic.

---

# 8. Agent Architecture

The initial architecture should prefer:

One capable orchestrator agent + explicit tools

over:

Multiple autonomous agents

Do not add multiple agents purely for architectural complexity or marketing value.

The orchestrator should:

1. understand the user's question,
2. generate or update an investigation plan,
3. select tools,
4. inspect tool results,
5. collect evidence,
6. form hypotheses,
7. produce conclusions,
8. recommend actions.

Agent state should remain inspectable.

Important state may include:

* query
* plan
* observations
* tool executions
* evidence
* hypotheses
* conclusions
* recommendations

---

# 9. Tool Design Rules

Every agent tool must have:

* a clear purpose,
* explicit input schema,
* explicit output schema,
* documented failure states,
* permission boundaries,
* no hidden side effects.

Examples:

* search_documents
* query_database
* calculate_metric
* analyze_feedback
* generate_chart

LLMs must not directly access database credentials.

---

# 10. SQL Safety Rules

LLM-generated SQL must never execute without validation.

Initial analytics queries must be read-only.

The SQL execution layer should enforce:

* SELECT-only access
* read-only database credentials
* table allowlists where appropriate
* query timeout
* row/result limits
* syntax validation
* protection against stacked queries
* execution error handling

Do not allow:

* INSERT
* UPDATE
* DELETE
* DROP
* ALTER
* TRUNCATE
* CREATE

unless a future explicitly authorized action system requires it.

---

# 11. Evidence First

OpsPilot conclusions should be traceable to evidence.

Important factual claims should reference their source whenever possible.

Evidence may originate from:

* database query results
* CSV rows or aggregations
* document chunks
* PDF pages
* analytical calculations

Do not fabricate citations.

Do not create evidence after generating the answer merely to justify it.

Evidence collection must be part of the investigation process.

---

# 12. RAG Principles

The retrieval system should ultimately support:

Query
→ Query Processing / Rewrite
→ Keyword Retrieval

* Vector Retrieval
  → Fusion
  → Reranking
  → Context Selection
  → Generation

Do not assume vector similarity alone is sufficient.

Retrieval quality must eventually be evaluated against a known evaluation dataset.

---

# 13. Data Analytics Principles

Natural-language analytics should follow a controlled workflow:

Question
→ Dataset Selection
→ Schema Inspection
→ Analysis Plan
→ SQL / Analytical Tool
→ Execution
→ Validation
→ Interpretation

The LLM should reason over computed results rather than invent numerical conclusions.

All important calculated values should originate from deterministic computation.

---

# 14. Background Jobs

Long-running operations should not unnecessarily block HTTP requests.

Potential background tasks include:

* document parsing
* embedding generation
* indexing
* large dataset ingestion
* investigations
* evaluation runs

The exact architecture should remain as simple as possible.

Do not introduce asynchronous infrastructure before it is needed.

---

# 15. Coding Principles

Prefer:

* simple code
* explicit behavior
* small focused functions
* typed interfaces
* dependency injection where useful
* clear domain naming
* testable services
* predictable errors

Avoid:

* unnecessary abstractions
* speculative abstractions
* premature optimization
* giant service classes
* deeply nested logic
* duplicated business rules
* clever code that reduces readability

---

# 16. Python Guidelines

Use Python type hints.

Use Pydantic models for API/domain boundaries when appropriate.

Prefer async I/O where the underlying operation is genuinely asynchronous.

Do not mark functions async without reason.

Use clear exception types.

Do not silently swallow exceptions.

---

# 17. Frontend Guidelines

The frontend should prioritize the investigation experience.

Important interfaces include:

* data source management
* investigation workspace
* live investigation progress
* evidence viewer
* charts
* execution details
* observability panels

Do not spend excessive development time on decorative UI before core functionality works.

---

# 18. Testing Principles

Every important deterministic component should be testable independently.

Prioritize tests around:

* parsing
* chunking
* retrieval
* SQL validation
* analytical calculations
* tool contracts
* evidence mapping
* API behavior

Important workflows should have integration tests.

Core demo investigations should eventually have end-to-end evaluation cases.

Never delete or weaken tests simply to make the test suite pass.

---

# 19. Security Principles

Follow least privilege.

Important areas include:

* file upload validation
* SQL injection
* prompt injection
* indirect prompt injection from documents
* tool permissions
* secrets management
* database permissions
* authentication
* authorization
* untrusted generated content

Treat uploaded documents and dataset contents as untrusted data.

Instructions contained inside business documents must not override system or application rules.

---

# 20. Observability

Important AI workflows should eventually record:

* model
* execution duration
* LLM calls
* tool calls
* tool failures
* token usage
* estimated cost
* retrieved chunks
* retrieval scores
* reranking information
* investigation steps

Observability must help debugging rather than exist only as UI decoration.

---

# 21. Documentation Rules

Documentation is part of the project.

Relevant documentation should be updated when implementation changes architecture or behavior.

Important files include:

* CLAUDE.md
* PRODUCT.md
* ARCHITECTURE.md
* ROADMAP.md
* BACKLOG.md
* DATA_MODEL.md
* DATASET.md
* RAG_SYSTEM.md
* AGENT_SYSTEM.md
* ANALYTICS_ENGINE.md
* API.md
* TESTING.md
* SECURITY.md
* DECISIONS.md

Do not modify architecture silently.

When making a significant architectural decision, document it in DECISIONS.md.

---

# 22. Development Workflow

Before implementing a meaningful feature:

1. Read CLAUDE.md.
2. Read the relevant architecture/domain documents.
3. Inspect the existing repository.
4. Identify affected modules and files.
5. Understand existing patterns.
6. Produce a concise implementation plan.
7. Identify risks and architectural implications.
8. Implement only after the plan is approved when approval has been requested.
9. Add or update tests.
10. Run relevant tests.
11. Run formatting/lint/type checks where available.
12. Update relevant documentation.
13. Report what changed and any unresolved concerns.

---

# 23. Task Scope Rules

Only modify code required for the current task.

Do not:

* rewrite unrelated modules,
* perform large refactors without permission,
* change technology choices silently,
* add unrelated features,
* change public contracts unnecessarily,
* remove functionality without explanation.

If an adjacent issue is discovered, report it separately.

---

# 24. Never Fake Functionality

Do not:

* hardcode investigation answers,
* hardcode demo conclusions,
* fabricate AI outputs,
* return fake analytics,
* create placeholder success paths and present them as complete,
* silently mock production behavior.

Mocks are allowed only in tests or explicitly identified development environments.

The Northstar Commerce demo must be solved through the same real system used for other investigations.

---

# 25. Definition of Done

A feature is not complete merely because code has been written.

A feature is done when applicable:

* implementation is complete,
* relevant tests pass,
* error paths are handled,
* types/contracts are correct,
* documentation is updated,
* the feature is manually or automatically verified,
* no known critical regression remains.

---

# 26. Learning-Oriented Development

This project is being built with AI assistance, but the human developer intends to understand the resulting system.

Therefore:

* favor understandable implementations,
* explain unusual architecture in code comments or documentation where useful,
* avoid unnecessary magic,
* identify important concepts introduced by a task,
* clearly report non-obvious tradeoffs,
* do not hide complexity behind opaque generated code.

When requested, explain the implementation from first principles rather than only describing what files changed.
