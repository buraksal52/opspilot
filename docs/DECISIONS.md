# OpsPilot — Architecture Decisions

This document records important technical and architectural decisions.

Each decision should include:

* Context
* Decision
* Rationale
* Alternatives
* Consequences

Do not silently change a recorded decision.

If a decision changes, add a new ADR entry that supersedes the previous one.

---

# ADR-001 — Use a Modular Monolith

## Context

OpsPilot includes several logical domains:

* ingestion
* retrieval
* analytics
* agents
* investigations
* evidence
* observability
* evaluation

A microservice architecture could separate these concerns physically, but the initial product is a portfolio-quality application with limited operational scale requirements.

## Decision

Use a modular monolith.

Keep clear internal module boundaries while deploying the backend as one primary application.

## Rationale

Benefits:

* simpler development
* easier debugging
* lower infrastructure complexity
* easier local setup
* easier refactoring
* better learning experience
* reduced operational overhead

The project currently has no scaling requirement that justifies microservices.

## Alternatives

### Microservices

Rejected for V1.

Would introduce:

* distributed tracing complexity
* service networking
* deployment complexity
* cross-service contracts
* more difficult local development

without providing meaningful current value.

## Consequences

Modules must still maintain clear responsibilities.

Avoid creating a monolith with tightly coupled internal code.

---

# ADR-002 — FastAPI for Backend API

## Context

OpsPilot requires:

* AI integration
* data processing
* async I/O
* Python ML/data libraries
* typed API contracts

## Decision

Use FastAPI as the primary backend framework.

## Rationale

Advantages:

* Python AI ecosystem compatibility
* Pydantic integration
* async support
* automatic OpenAPI generation
* concise API development
* strong suitability for AI/data applications

## Alternatives

### Go

Strong for backend performance and concurrency, but would increase friction with AI and data tooling in this project.

### Django

Provides more built-in application functionality than OpsPilot currently requires.

## Consequences

Backend code should remain modular enough that heavy compute workloads can later be separated if necessary.

---

# ADR-003 — PostgreSQL as Primary Database

## Context

OpsPilot requires storage for:

* application entities
* structured business data
* investigation state
* evidence
* execution metadata
* vector embeddings

## Decision

Use PostgreSQL as the primary durable datastore.

## Rationale

PostgreSQL provides:

* relational integrity
* analytical SQL support
* mature indexing
* JSONB
* strong ecosystem
* pgvector compatibility

## Alternatives

### MongoDB

Rejected because core application data and structured analytics benefit more from relational modeling.

### Multiple databases

Rejected for V1 to avoid unnecessary operational complexity.

## Consequences

Database schema boundaries must remain explicit.

---

# ADR-004 — Use pgvector for Vector Storage

## Context

OpsPilot requires semantic search over document chunks.

## Decision

Store document embeddings in PostgreSQL using pgvector.

## Rationale

Benefits:

* avoids separate vector infrastructure
* keeps metadata and embeddings close together
* simpler local development
* sufficient for project scale
* easy transactional consistency

## Alternatives

### Qdrant

### Pinecone

### Weaviate

Potential future options if scale or retrieval requirements justify them.

## Consequences

Vector indexing and similarity configuration should be evaluated during RAG implementation.

---

# ADR-005 — Use Redis for Temporary Coordination and Caching

## Context

Some operations may benefit from:

* caching
* background-job coordination
* temporary state
* rate limiting
* execution event delivery

## Decision

Use Redis where such functionality is justified.

## Rationale

Redis is widely supported and appropriate for ephemeral operational state.

## Important Constraint

Redis must not become the primary durable datastore.

## Consequences

Each Redis use should have a clear reason.

Do not store critical state only in Redis.

---

# ADR-006 — One Orchestrator Agent for V1

## Context

OpsPilot needs AI-driven investigation planning and tool use.

A multi-agent architecture may appear attractive.

## Decision

Use one orchestrator agent with explicit tools for V1.

## Rationale

Advantages:

* simpler reasoning flow
* easier debugging
* easier evaluation
* lower token usage
* clearer state
* fewer coordination failures

Multi-agent systems should only be introduced if a demonstrated workflow requires specialization.

## Alternatives

### Multi-Agent Swarm

Rejected for initial implementation due to unnecessary complexity.

## Consequences

Agent tool design becomes especially important.

The orchestrator must remain inspectable.

---

# ADR-007 — AI Must Use Explicit Tools

## Context

OpsPilot must interact with structured and unstructured business data.

## Decision

LLMs cannot directly access databases, filesystems, credentials, or infrastructure.

All interactions must occur through explicit application-defined tools.

## Rationale

Provides:

* permission control
* validation
* observability
* testability
* safer execution

## Consequences

Tool interfaces must use structured input and output schemas.

---

# ADR-008 — SQL Analytics Must Be Read-Only

## Context

OpsPilot will generate analytical SQL from natural-language questions.

Generated SQL is untrusted.

## Decision

V1 AI analytics can execute only read-only queries.

## Controls

Enforce:

* read-only database role
* SELECT-only validation
* table allowlist
* query timeout
* result limits
* rejection of stacked queries

## Alternatives

Allow write queries.

Rejected because V1 is focused on investigation, not autonomous database modification.

## Consequences

Future action execution must use separate controlled tools.

---

# ADR-009 — Separate Application and Analytics Schemas

## Context

OpsPilot stores both:

1. its own application state
2. user/demo business datasets

Mixing both creates unclear boundaries.

## Decision

Separate them conceptually using schemas.

Recommended:

```text
app.*
analytics.*
```

## Rationale

Benefits:

* clearer security
* easier table allowlisting
* cleaner organization
* safer AI query boundaries

## Consequences

Analytics SQL tools should only access allowed analytics schemas.

This decision is settled, not open — see ADR-017 for how physical tables within the `analytics` schema are generated and allowlisted per Dataset/workspace, which builds directly on this schema separation.

---

# ADR-010 — SSE for Investigation Progress

## Context

The frontend needs live investigation progress.

Most communication is server → client.

## Decision

Use Server-Sent Events initially.

## Rationale

SSE is simpler than WebSockets when bidirectional real-time communication is not necessary.

## Alternatives

### WebSockets

May be introduced later if requirements become genuinely interactive.

## Consequences

Event structure must be explicit and documented.

---

# ADR-011 — Structured AI Outputs Where Behavior Depends on AI

## Context

Free-form model output is unreliable for application control flow.

## Decision

Whenever AI output affects program logic, require structured output.

Examples:

* investigation plans
* tool requests
* findings
* recommendations
* query intent

## Rationale

Improves:

* validation
* reliability
* observability
* testing

## Consequences

Human-readable prose should normally be generated after structured reasoning state exists.

---

# ADR-012 — Evidence Must Be Collected During Investigation

## Context

It is easy for an LLM to generate a conclusion first and attach plausible sources afterward.

## Decision

Evidence must be collected as part of tool execution and investigation state.

## Rationale

Improves grounding and reduces fabricated justification.

## Consequences

Final claims should reference previously recorded evidence.

---

# ADR-013 — Northstar Data Must Be Reproducible

## Context

The demo dataset is used for both development and evaluation.

Randomly changing data would make debugging unreliable.

## Decision

Synthetic dataset generation must use deterministic seeds.

## Consequences

The same dataset can be recreated for testing and demonstrations.

---

# ADR-014 — Do Not Execute Arbitrary Generated Python

## Context

An AI analytics product could execute generated Python code.

This provides flexibility but creates security and reproducibility problems.

## Decision

Do not support unrestricted AI-generated Python execution in V1.

Use explicit analytical tools and SQL instead.

## Alternatives

Sandboxed Python execution may be evaluated later.

## Consequences

Some advanced analyses may require dedicated deterministic tool implementations.

---

# ADR-015 — Use Provider Abstractions for AI Models

## Context

Model providers and model quality evolve rapidly.

## Decision

Core business logic must not depend directly on a specific provider.

Use narrow provider interfaces.

## Consequences

Provider-specific features should not leak widely through the application.

---

# ADR-016 — Correctness Before Autonomy

## Context

OpsPilot could eventually execute operational actions.

## Decision

Initial product prioritizes investigation and recommendation.

External side effects are deferred.

## Rationale

Reliable analysis must exist before trustworthy automation.

## Consequences

The architecture should permit future action tools but not prematurely implement them.

---

# ADR-017 — Per-Dataset Generated Analytics Tables With Dynamic Workspace-Scoped SQL Allowlist

## Context

DATA_MODEL.md and ANALYTICS_ENGINE.md previously described two incompatible physical storage strategies for uploaded structured datasets: a per-Dataset generated `table_name` field, and fixed canonical shared table names (e.g. `analytics.orders`) illustrated as if one physical table existed per business concept across the whole system. Neither version specified workspace-level isolation inside the analytics schema, which left an open cross-tenant data-access risk in the SQL execution path that ADR-008 and ADR-009 depend on.

## Decision

Each uploaded structured Dataset is materialized into its own generated PostgreSQL table under the `analytics` schema (one table per Dataset, not one shared table per business concept).

Physical table and column identifiers are generated by the application. They are never derived directly from user-provided filenames or CSV headers. The original user-facing names are preserved separately as display metadata on the Dataset/column definitions.

The SQL execution layer does not use a fixed, hardcoded table allowlist. It builds the allowlist dynamically, per request, from the set of Dataset records belonging to the requesting workspace. AI-generated queries may reference only the physical tables present in that dynamically built, workspace-scoped allowlist.

## Rationale

* removes the shared-table collision problem when multiple workspaces upload similarly-named datasets (e.g. two workspaces each uploading `orders.csv`),
* removes the SQL-identifier-injection surface created by interpolating user-controlled names into DDL,
* makes workspace isolation an enforced property of query validation rather than an assumption layered on top of a static list,
* keeps the analytics schema boundary (ADR-009) meaningful under multi-dataset, multi-workspace growth.

## Alternatives

### Fixed canonical shared tables per business concept

Rejected. Cannot support multiple workspaces or multiple uploads of the same logical dataset type, and implicitly requires row-level `workspace_id` filtering that was never specified.

### Physical table/column names derived directly from user filenames or CSV headers

Rejected. Creates a SQL-identifier-injection risk at ingestion time (DDL), separate from and not covered by the agent-generated-SQL validation pipeline.

## Consequences

* Dataset catalog and schema-context construction (ANALYTICS_ENGINE.md) must resolve logical/display dataset names to generated physical tables scoped to the current workspace.
* Ingestion (Phase 3) must generate and persist sanitized physical identifiers alongside the original display name.
* This supersedes the fixed-shared-table illustration previously implied by DATA_MODEL.md §9 and the static allowlist wording previously implied by SECURITY.md §13.

---

# ADR-018 — Defer Background Worker Technology Selection to Phase 3

## Context

ARCHITECTURE.md requires that the background worker implementation be documented through an ADR before adoption, and several flows (PDF parsing, embedding generation, large dataset ingestion) are expected to eventually run outside the HTTP request lifecycle. No worker technology has been evaluated yet, and Phase 1/2 do not require one.

## Decision

Do not select a background worker library during Phase 0, 1, or 2.

The decision is explicitly deferred to the beginning of Phase 3 (Data Ingestion), which is the first phase where asynchronous processing (document parsing, later embedding generation) becomes relevant.

A task to evaluate and select the worker technology is tracked at the start of the Phase 3 backlog. Phase 1 and Phase 2 must not implicitly depend on any specific worker implementation.

## Rationale

* avoids picking infrastructure before the workloads that justify it exist,
* keeps Phase 1 (project foundation) and Phase 2 (dataset generation) free of a dependency they don't need,
* matches ROADMAP.md's "avoid premature complexity" principle.

## Alternatives

Select a worker technology now (e.g. Celery, arq, RQ). Rejected — no real workload exists yet to validate the choice against, and Phase 1/2 have no async requirement.

## Consequences

* Phase 3 cannot be marked done until this ADR is superseded by an actual technology decision.
* Until then, any Phase 3 document/CSV ingestion work must be scoped so it does not assume a specific worker framework is present.

---

# ADR-019 — V1 Authentication Strategy

## Context

PRODUCT.md, SECURITY.md, API.md, and DATA_MODEL.md all deferred the exact V1 authentication approach to "implementation time." The User/Workspace ownership model and every workspace-scoped authorization check (SECURITY.md §4) depend on this being settled before Phase 1 implements the User model.

## Decision

V1 uses email/password authentication with the following concrete choices:

* **Credentials:** email + password. No social login, no Google OAuth, no enterprise SSO, no magic links.
* **Password storage:** passwords are stored only as Argon2 hashes, generated and verified via **pwdlib** (configured to use Argon2). Plaintext passwords are never persisted, logged, or retained anywhere, including in traces (SECURITY.md §28–29).
* **Session mechanism:** stateless JWT bearer access tokens, issued and verified using **PyJWT**. Tokens are sent by the client as a standard `Authorization: Bearer <token>` header. No server-side session store is introduced for V1 — no session table, no Redis-backed session state.
* **Authorization model:** authentication resolves the current User from the JWT; authorization is then enforced server-side per request using `Workspace.owner_id` (DATA_MODEL.md §4) — a user may only access a workspace's resources if they own it. This satisfies the "User → Workspace authorization" requirement without a role/membership system.
* **Explicitly out of scope for V1:** social login, Google OAuth, enterprise SSO, magic links, complex/multi-role systems (owner/analyst/viewer remains a future extension per SECURITY.md §6).

## Rationale

* Argon2 (via pwdlib) is the current recommended password-hashing algorithm and avoids hand-rolling hashing/salting.
* JWT + PyJWT keeps the implementation minimal and stateless, matching "authentication remains intentionally minimal" — no session infrastructure needs to be built or secured for V1.
* `owner_id`-based authorization reuses a field the data model already has, rather than introducing a membership/role entity before the product needs one (CLAUDE.md §15, §23).

## Alternatives

* **Hosted auth provider (e.g. Auth0, Clerk):** rejected for V1 — adds an external dependency and account-setup overhead disproportionate to a single-owner-per-workspace portfolio demo.
* **Server-side sessions (cookie + session store):** rejected — would require Redis/DB-backed session state for no clear V1 benefit over stateless JWTs.
* **Role/membership system (owner/analyst/viewer):** rejected for V1 — explicitly out of scope; `owner_id` is sufficient until multi-member workspaces are a real requirement.

## Consequences

* `User` gains a `hashed_password` field (DATA_MODEL.md §3); no plaintext password field ever exists.
* No session/token table is added to the data model — JWTs are self-contained and not persisted server-side. This means V1 has no server-side token revocation; a compromised token remains valid until it expires. This limitation must be documented (SECURITY.md §5), not silently accepted.
* The JWT signing secret is a secret per SECURITY.md §7 (never committed, loaded from environment).
* API endpoints requiring authentication use the standard `Authorization: Bearer <token>` header (API.md §19).
* Every workspace-scoped API handler must resolve the authenticated user and check `Workspace.owner_id` before returning or mutating any workspace-owned resource (SECURITY.md §4).

---

# ADR-020 — Database Access Strategy: SQLAlchemy 2.x + Alembic

## Context

BACKLOG.md Phase 1.3 required an ORM/database-layer selection before Phase 1 foundational models could be implemented. OpsPilot also has two structurally different persistence needs: normal CRUD-style application-domain entities (User, Workspace, DataSource, Document, DocumentChunk, Dataset metadata, Investigation, InvestigationStep, ToolExecution, Evidence) versus dynamically generated per-Dataset analytics tables (ADR-017) whose physical shape is only known at runtime, not at code-authoring time.

## Decision

Use **PostgreSQL** with **SQLAlchemy 2.x** as the sole database toolkit, and **Alembic** for migrations.

* Use SQLAlchemy's **ORM** (declarative models) for normal application-domain persistence — the entities listed above, living in the `app` schema (ADR-009).
* Use SQLAlchemy **Core** (or other explicit, parameterized SQLAlchemy constructs — reflection, `text()` with bound parameters, `Table` objects built from sanitized identifiers) for dynamic analytics-table operations, where the table/column shape is only known at runtime and does not fit a compile-time-known ORM model. This covers Dataset ingestion DDL and AI-generated analytical query execution (ADR-017).
* Use **async** database access (SQLAlchemy's async engine, e.g. with `asyncpg`) where the operation is genuinely I/O-bound and sits on a request path that benefits from it (e.g. API handlers), per CLAUDE.md §16 ("do not mark functions async without reason"). Synchronous access remains acceptable for tooling/scripts (e.g. the Northstar dataset generator) where async offers no benefit.
* Do not introduce a second ORM or query-builder library for the analytics path — SQLAlchemy Core already covers dynamic, runtime-defined table access without a second dependency.

## Rationale

* One toolkit for both access patterns (Core and ORM share the same engine/connection/transaction machinery in SQLAlchemy 2.x), avoiding a second library purely for the analytics path.
* Alembic is the standard, actively maintained migration tool for SQLAlchemy and integrates directly with its metadata.
* Forcing an ORM declarative model onto tables whose shape is generated per-Dataset at runtime (ADR-017) would be awkward and would encourage exactly the kind of dynamic-identifier string-building that SECURITY.md's identifier-injection rule (§24) forbids; SQLAlchemy Core's parameterized, identifier-quoting constructs are the correct fit there instead.
* Async where the request path benefits, sync where it doesn't, avoids reflexive `async def` usage with no I/O benefit.

## Alternatives

* **Raw psycopg without any query builder:** rejected — loses migration tooling and typed model boundaries for the majority of the codebase, which is normal CRUD persistence.
* **A second lightweight query builder for the analytics path (e.g. raw string templates):** rejected — reintroduces the identifier-injection risk SECURITY.md §24 and ADR-017 specifically close off; SQLAlchemy Core already provides safe, parameterized primitives for this.
* **Django ORM:** rejected — already rejected at the framework level (ADR-002); would also require a second, incompatible toolkit alongside FastAPI.

## Consequences

* Alembic migrations manage only the `app` schema's ORM-mapped tables. Per-Dataset `analytics.*` physical tables (ADR-017) are created/altered/dropped programmatically at ingestion time via SQLAlchemy Core, not through Alembic revisions — their schema is data, not code.
* All dynamically generated analytics DDL/DML must use SQLAlchemy Core's identifier-quoting and parameter-binding facilities; string-concatenated SQL against user-derived names remains forbidden regardless of toolkit (SECURITY.md §24).
* Repository/service boundaries (ARCHITECTURE.md §5, Infrastructure Layer) wrap SQLAlchemy sessions/engines; domain and application layers must not import SQLAlchemy models directly outside the infrastructure layer's repositories.

---

# ADR-021 — Finalized V1 Repository Layout

## Context

ARCHITECTURE.md previously offered a "suggested" repository structure with a separate top-level `services/*` tree (`services/ingestion/`, `services/retrieval/`, etc.) alongside `apps/api/`, and explicitly left "the exact Python package layout... to evolve during Phase 1." BACKLOG.md's Phase 0 gate required the layout to be confirmed before Phase 1 begins.

## Decision

Adopt the following as the **approved** V1 structure, not a suggestion:

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

Backend application code lives under `apps/api/app/`, organized by **logical layer** (matching CLAUDE.md §4 and ARCHITECTURE.md §5's API → Application → Domain → Infrastructure layering), not by business module. Business modules (ingestion, retrieval, analytics, agents, investigations, evidence, evaluation, observability) are organized as subpackages *within* `domain/`, `application/`, and `infrastructure/` — there is no separate top-level `services/*` tree. Frontend code lives under `apps/web/`.

## Rationale

* A single layering scheme (layer-first, under `apps/api/app/`) is simpler to navigate than two competing schemes (the earlier draft's layer folders *and* a parallel `services/*` module tree).
* Each backend logical layer from ARCHITECTURE.md §5 gets exactly one corresponding package, so "where does this code go" has one answer.
* Keeps `scripts/` (e.g. the Northstar dataset generator) and `infra/` (Docker/compose) as clearly non-application-code concerns at the top level.

## Alternatives

* **The originally-sketched `services/ingestion/`, `services/retrieval/`, ... top-level tree:** superseded. It duplicated the layering already expressed inside `apps/api/app/` and risked modules being organized inconsistently (some by layer, some by business concern).

## Consequences

* Do not create empty placeholder subpackages for a business module before it has real code — create `application/investigations/`, `infrastructure/retrieval/`, etc. when their first real file is added, not upfront (CLAUDE.md §15, avoiding speculative abstraction).
* `tests/` mirrors the structure already specified in TESTING.md §3 and is unaffected by this ADR.

---

# ADR-022 — Disposable Docker Containers for Backend Test Infrastructure

## Context

Phase 1 introduced the first database- and Redis-backed automated tests (`tests/api`, `tests/integration`). TESTING.md §29 says to prefer small deterministic fixtures and does not mandate a specific mechanism for providing PostgreSQL/Redis to those tests. A concrete choice was needed: run tests against the same `docker compose` stack developers use locally, use an in-process substitute (e.g. SQLite for Postgres), or use dedicated, disposable containers.

## Decision

Backend tests always run against short-lived, dedicated Docker containers (`opspilot-test-pg`, `opspilot-test-redis`), started and torn down by `make test-api` (`Makefile` `test-infra-up`/`test-infra-down` targets), never against the `docker compose` dev stack (`docker-compose.yml`'s `postgres`/`redis` services).

* `tests/conftest.py` points at these containers via `TEST_DATABASE_URL`/`REDIS_URL` (defaulting to ports `55432`/`63790`, distinct from the dev stack's `5432`/`6379`, so both can run concurrently without conflict).
* The session-scoped fixture runs the real Alembic migration chain (`alembic upgrade head` / `downgrade base`) against the test container — not `Base.metadata.create_all()` — so migrations themselves are exercised as part of every test run, not just implicitly trusted.
* Real PostgreSQL (not SQLite) is used so Postgres-specific behavior (schemas, `gen_random_uuid`/`Uuid` type mapping, constraint semantics) matches production.

## Rationale

* Running tests against the dev `docker compose` stack was rejected because the fixture teardown runs `alembic downgrade base`, which drops the `app`/`analytics` schemas — acceptable for a disposable container, destructive if pointed at a developer's persistent local data.
* SQLite would not exercise the actual PostgreSQL dialect (schemas, constraint behavior) the application depends on, undermining confidence that passing tests reflect real Postgres behavior.
* A dedicated testcontainers-style library was considered unnecessary added dependency weight for V1 — two `docker run` commands in the `Makefile` achieve the same isolation with no new Python dependency.

## Alternatives

* **Reuse the `docker compose` dev stack for tests:** rejected — destructive teardown risk against real local dev data.
* **SQLite in-memory database for tests:** rejected — does not validate actual PostgreSQL schema/constraint behavior.
* **`testcontainers` Python library:** deferred — plain `docker run`/`docker rm` in the `Makefile` is sufficient for V1 and avoids an additional dependency; may be revisited if test infra needs grow (e.g. parallel test workers needing per-worker containers).

## Consequences

* `make test-api` is the standard way to run backend tests locally; running `pytest tests/` directly requires the developer to have already started matching Postgres/Redis instances on the expected ports (or overridden `TEST_DATABASE_URL`/`REDIS_URL`).
* CI must run `make test-api` (or equivalent container setup) rather than assuming a pre-existing database.
* This pattern should be followed for any future test suites needing PostgreSQL/Redis (e.g. Phase 3+ ingestion tests), rather than introducing a second, inconsistent mechanism.
* This supersedes ARCHITECTURE.md §6's earlier "suggested... may evolve" framing; the structure above is now the reference layout for Phase 1 scaffolding.

---

# ADR-023 — Northstar Dataset Generator: Location, Dependencies, and Output Handling

## Context

BACKLOG.md Phase 2 required a deterministic generator for the Northstar Commerce demo dataset (DATASET.md): five CSVs, five business documents, `ground_truth.json`, and the canonical `evaluation_questions.json` question bank (DATASET.md §33). Three implementation questions were not yet settled: where the generator code lives relative to `apps/api` (ADR-021's approved layout only covers application code), whether it needs its own Python environment, and whether its output belongs in version control.

## Decision

* **Location:** the generator lives at `scripts/northstar/` as a plain Python package (stdlib-only for CSV/JSON generation — no Faker/pandas/numpy). This matches ADR-021, which already carves out `scripts/` as a non-application-code concern separate from `apps/api/app/`'s layered structure.
* **Python environment:** the generator reuses `apps/api/.venv` rather than getting its own virtualenv. `pytest.ini`'s `pythonpath` was extended to `apps/api scripts` so `tests/unit/test_northstar_generator.py` can `import northstar.*` through the same environment `make test-api` already uses. A second venv was judged unjustified process overhead for a single-purpose script package.
* **PDF dependency isolation:** DATASET.md §19 names the five business documents with a `.pdf` extension, and Phase 3's PDF parser needs real PDF fixtures to test against, so documents are rendered as PDF (via `fpdf2`, pure-Python, no transitive dependencies) in addition to their Markdown source. `fpdf2` is declared only under `apps/api/pyproject.toml`'s `[project.optional-dependencies] dev` extra, never as a core dependency — the Dockerfile's `pip install .` does not install extras, so it never reaches the deployed API image.
* **Generated output is not committed to git.** `data/northstar/` (CSVs, documents, `ground_truth.json`, `evaluation_questions.json`, `validation_report.json`) is gitignored and reproduced on demand via `make generate-northstar`, which refuses to write output at all if `northstar.validate` reports any failing check (DATASET.md §30).
* **Ground truth and evaluation-question values are computed, not hand-typed.** `northstar.metrics` is the single source of the "actual" numbers (refund rates, delivery-day averages, ticket shares) consumed by both `ground_truth.json` and the `analytics`-tagged questions in `evaluation_questions.json`, so the two files can never silently drift apart from what the generator actually produced.

## Rationale

* Reuses existing, working tooling (`apps/api/.venv`, `pytest.ini`, `make test-api`) instead of introducing a second Python environment and a second test-runner entry point for one script package (CLAUDE.md §15, avoid unnecessary abstractions).
* Keeps the deployed API's dependency surface unchanged — a PDF-rendering library has no business being importable at API runtime (SECURITY.md §35, dependency additions must be justified).
* A deterministic, seeded generator makes committing its output redundant: anyone can reproduce byte-identical CSVs via `make generate-northstar` (verified: two runs with the default seed produce identical CSV/ground-truth output), and gitignoring it keeps the repository free of large generated artifacts.
* Deriving `ground_truth.json` and the analytics evaluation questions from the same `northstar.metrics` computation (rather than both copying DATASET.md's target *ranges* by hand) means evaluation always checks against what the dataset actually contains, not an aspirational target that generation might miss.

## Alternatives

* **A dedicated `scripts/pyproject.toml` and separate venv:** rejected — adds a second dependency-management surface and Makefile activation path for no benefit at V1 scale.
* **Committing `data/northstar/` to the repository:** considered, for interview/portfolio reproducibility without a generation step. Rejected in favor of `make generate-northstar` being fast (~1 second) and fully deterministic, which makes "regenerate on demand" equivalent to "already there" without repository bloat. May be revisited in Phase 12 (Polish & Portfolio) if a zero-setup clone-and-run demo is judged more valuable than a lean repository.
* **Hardcoding DATASET.md's target ranges directly into `ground_truth.json`:** rejected — would silently pass even if the generator's actual output drifted from those targets; computing from real generated data makes ground truth self-consistent with the dataset it describes.

## Consequences

* `make generate-northstar` must run (implicitly or explicitly) before any Phase 3+ work that consumes `data/northstar/` (ingestion tests, RAG/analytics/agent evaluation) — it is not a one-time setup step to forget about.
* Any future script requiring dependencies not already in `apps/api/.venv` should default to the same `dev`-extras-isolation pattern established here, rather than inventing a new per-script environment.
* `northstar.metrics` is now a de facto contract: Phase 3+ code that needs "the same numbers the demo dataset was validated against" should call into it rather than recomputing equivalent logic independently.

---

# ADR-024 — Background Worker Technology: arq Selected, Activation Deferred to Phase 4

## Context

ADR-018 deferred selecting a background worker technology to "the beginning of Phase 3," and BACKLOG.md's Phase 3.0 gate requires that selection be made and recorded before Phase 3 (Data Ingestion) proceeds. The candidate workloads are PDF parsing and CSV ingestion (Phase 3) and embedding generation (Phase 4).

## Decision

* **Technology selected:** [arq](https://github.com/samuelcolvin/arq) — an async, Redis-backed job queue.
* **Activation deferred to Phase 4.** Phase 3 does not stand up arq or any worker process. Document and dataset ingestion (PDF/Markdown/text parsing, CSV parsing + physical table creation) run **synchronously inside the upload request**. The upload endpoint still returns a `DataSource` immediately in `UPLOADED` status and transitions it through `PROCESSING` before returning (API.md §6's "processing may continue asynchronously" is a permitted response shape, not a requirement — V1 chooses the simpler synchronous path since it is also correct at this scale).

## Rationale

* Northstar-scale inputs are small: five business documents (each well under a second to parse with `pypdf`) and CSVs up to ~15,000 rows (well under a second to parse and bulk-insert). There is no request-latency problem to solve yet.
* CLAUDE.md §14 / ROADMAP.md §2: "do not introduce asynchronous infrastructure before it is needed." Standing up Redis-backed job dispatch, a worker process, Docker Compose changes, and job-status polling for a sub-second operation would be complexity without a corresponding benefit.
* arq is selected now (rather than re-opening the evaluation in Phase 4) because the workload that actually needs it — embedding generation, potentially over large document sets, genuinely slow relative to a request lifecycle — is already known from RAG_SYSTEM.md §4/§12. arq fits the project's existing choices: async-native (consistent with ADR-020's async SQLAlchemy engine on request paths), Redis-backed (Redis is already a dependency per ADR-005), and it is significantly lighter to operate than Celery (no separate broker beyond the Redis instance already running, no additional exchange/queue configuration).

## Alternatives

* **Celery:** rejected — heavier operationally (typically wants a dedicated broker configuration and its own monitoring), and its worker model is synchronous-first, which fights against this codebase's async-first request path (ADR-020).
* **RQ (Redis Queue):** a reasonable lighter-weight alternative to Celery, but synchronous rather than async; arq is effectively "RQ's ideas, async" and fits better alongside FastAPI's async handlers.
* **FastAPI `BackgroundTasks`:** rejected as the long-term answer — it runs in-process with no persistence, retry, or cross-process visibility, which ARCHITECTURE.md §4 (Background Worker) and SECURITY.md §32 (bounded retries, resource exhaustion controls) both expect a real job system to provide. Acceptable only as what Phase 3 already does today: no queue at all, plain synchronous execution.
* **Selecting nothing yet, re-evaluating in Phase 4:** rejected — the evaluation itself is cheap and the workloads that justify a choice (RAG_SYSTEM.md's embedding pipeline) are already specified in enough detail to decide now; deferring again would just repeat ADR-018's deferral without new information arriving in the meantime.

## Consequences

* Phase 3 ingestion code (`application/ingestion/*`) must be written so moving it behind an arq task in Phase 4 is a wiring change, not a rewrite: ingestion logic lives in plain application-service methods that an API route calls directly today and an arq worker function can call identically later.
* Phase 4 (Retrieval/RAG) is the phase that must actually add arq to `docker-compose.yml`, define its worker entrypoint, and wire embedding generation through it. Phase 4 cannot be marked done on synchronous embedding generation alone if document volume makes that impractical.
* This supersedes ADR-018 in full; ADR-018 stays in this document for history but is no longer the operative decision.

---

# ADR-025 — Embedding Provider: Google Gemini (`gemini-embedding-001`)

## Context

RAG_SYSTEM.md §12 requires a narrow `EmbeddingProvider` abstraction (`embed_text`/`embed_batch`) so application logic does not depend on one vendor (ADR-015). No LLM or embedding provider had been selected anywhere in the project before Phase 4 — `core/config.py` and `.env.example` had no provider API key placeholder. Phase 4 (chunk embedding, query embedding) is the first place a concrete choice is required.

## Decision

Use **Google Gemini** as the V1 embedding provider:

* **Model:** `gemini-embedding-001`.
* **Output dimension:** `768`, requested via the model's `output_dimensionality` parameter (Matryoshka Representation Learning truncation). Stored as `EMBEDDING_DIMENSION` in settings so the pgvector column width and this choice cannot silently drift apart.
* **Task type:** the same `EmbeddingProvider.embed_batch(texts, task_type)` interface is used for both directions — `task_type="RETRIEVAL_DOCUMENT"` when embedding chunks at ingestion time, `task_type="RETRIEVAL_QUERY"` when embedding a search query. This is a parameter on one interface, not a vendor-specific branch in calling code.
* **SDK:** the `google-genai` Python package.
* **New secret:** `GEMINI_API_KEY` (SECURITY.md §7 — never committed; placeholder only in `.env.example`).
* `DocumentChunk.token_count` (DATA_MODEL.md §7) is populated by a simple, dependency-free chars/4 length heuristic, used only to size chunks against `CHUNK_TARGET_TOKENS`/`CHUNK_OVERLAP_TOKENS`. It is an approximation, not an exact Gemini token count — consistent with RAG_SYSTEM.md §9 describing the 400–700-token target as "starting values, not permanent architecture rules."

## Rationale

* Anthropic (the model family this environment runs on) does not publish its own embeddings API, so an embedding-specific vendor choice was unavoidable regardless of which LLM Phase 6 eventually picks for generation.
* Gemini's embedding model supports configurable output dimensionality and explicit retrieval task types, which map directly onto the asymmetric document/query embedding distinction RAG_SYSTEM.md's pipeline already implies without adding provider-specific concepts to the `EmbeddingProvider` interface itself.
* 768 dimensions keeps the pgvector column and any future ANN index (RAG_SYSTEM.md §18) reasonably sized for the Northstar-scale corpus while remaining a well-supported truncation point for this model family.

## Alternatives

* **OpenAI `text-embedding-3-small`:** rejected for now — no stronger fit than Gemini for this project, and the user's explicit choice was Gemini.
* **Voyage AI:** Anthropic's own recommended embedding partner; a reasonable alternative, not selected per explicit user direction.
* **Local `sentence-transformers` model (fully offline):** rejected — would add a heavy dependency (torch) to the deployed API image (SECURITY.md §35: dependency additions must be justified) for a benefit (no API key) that is not durable, since Phase 6's agent will need an LLM provider API key regardless.

## Consequences

* `app/infrastructure/embeddings/` holds the `EmbeddingProvider` protocol and the concrete `GeminiEmbeddingProvider`; a `FakeEmbeddingProvider` is used for all automated tests (TESTING.md §30 — no live paid API calls in normal test runs).
* `DocumentChunk.embedding` is a `pgvector.sqlalchemy.Vector(768)` column (ADR-004, ADR-026).
* Re-embedding at a different dimension or model in the future is an intentional re-indexing operation, not a silent mix of incompatible vector spaces (RAG_SYSTEM.md §14) — `embedding_model`/`embedding_version` on `DocumentChunk` record what produced each stored vector.

---

# ADR-026 — pgvector Postgres Image and arq Activation for Embedding Generation

## Context

ADR-004 chose pgvector for vector storage, but the Postgres image actually in use (`postgres:16-alpine`, both in `docker-compose.yml` and in `Makefile`'s disposable test containers, ADR-022) does not ship the `vector` extension binary — `CREATE EXTENSION vector` fails against it. Separately, ADR-024 selected arq as the background worker technology and explicitly named Phase 4 as "the phase that must actually add arq to `docker-compose.yml`... and wire embedding generation through it," with document/CSV parsing (Phase 3) staying synchronous by design.

## Decision

* Switch the Postgres image used by both the dev stack (`docker-compose.yml`) and the disposable test containers (`Makefile`'s `test-infra-up`) from `postgres:16-alpine` to **`pgvector/pgvector:pg16`** — the official image bundling the same Postgres 16 with the `vector` extension prebuilt. This is a direct, mechanical consequence of ADR-004, not a new architectural choice.
* Activate arq for embedding generation only, per ADR-024's already-recorded plan:
  * Document ingestion (`DocumentIngestionService`) still performs parsing and **chunking** synchronously inside the upload request — chunking is pure CPU work with no external I/O, same reasoning ADR-024 already applied to Phase 3 parsing.
  * `DocumentChunk.embedding` is created as `NULL` and filled in asynchronously: after chunks are persisted, an arq job (`generate_embeddings`, `app/infrastructure/jobs/tasks.py`) is enqueued for that document.
  * The task is a thin wrapper around `EmbeddingGenerationService.generate_for_document()` (`app/application/retrieval/embedding_service.py`) — the same service method is called directly by tests and by the manual evaluation script, so neither depends on a running worker process (mirrors the pattern ADR-024 already prescribed for ingestion).
  * All retrieval queries filter `WHERE embedding IS NOT NULL`, so a chunk whose embedding job hasn't run yet is simply not yet retrievable rather than causing an error.
  * A new `worker` service is added to `docker-compose.yml`, running `arq app.infrastructure.jobs.worker.WorkerSettings` against the same Postgres/Redis as `api`, bypassing `entrypoint.sh` (which hardcodes `alembic upgrade head` + uvicorn — only `api` should run migrations, to avoid two containers racing to migrate on startup).

## Rationale

* `pgvector/pgvector:pg16` is the pgvector project's own maintained image; adding the extension via a custom Dockerfile layer instead would duplicate work the upstream project already does correctly.
* Splitting "chunking" (sync) from "embedding" (async) at exactly the CPU/network-I/O boundary keeps the fast, deterministic part of ingestion inside the request/response cycle (so upload tests and UI status remain simple) while moving the genuinely slow, rate-limited, retryable part (RAG_SYSTEM.md §42, ARCHITECTURE.md §22) off the request path — this is the specific workload ADR-024 named as arq's justification.
* Nullable `embedding` + a `WHERE embedding IS NOT NULL` retrieval filter is simpler than adding a separate chunk-level or document-level "embedding status" enum, and requires no new status field on `Document`/`DataSource`.

## Alternatives

* **Build a custom Postgres image with `CREATE EXTENSION` scripting on top of `postgres:16-alpine`:** rejected — reinvents what `pgvector/pgvector:pg16` already provides, for no benefit.
* **Keep embedding generation synchronous inside the upload request (as Phase 3 did for parsing):** rejected — ADR-024 already committed Phase 4 to activating arq specifically for embedding generation; treating Gemini API latency/rate limits as acceptable inside a user-facing upload request would also work against RAG_SYSTEM.md §38's latency tracking intent and PRODUCT.md's demo responsiveness target.
* **A separate `Document.embedding_status` enum instead of nullable `DocumentChunk.embedding`:** deferred — adds a second source of truth to keep in sync with the actual per-chunk embedding state; revisit only if a product need for document-level "fully indexed" status emerges.

## Consequences

* `apps/api/pyproject.toml` gains `arq` and `pgvector` as core (non-dev) dependencies.
* `make test-api`'s disposable Postgres container now runs `pgvector/pgvector:pg16`; the Alembic migration introducing `DocumentChunk` includes `CREATE EXTENSION IF NOT EXISTS vector`.
* Local `make up` requires a real `GEMINI_API_KEY` in `.env` for the worker to actually produce non-null embeddings; without one, chunks are created but remain unembedded and therefore unretrievable, failing closed rather than silently returning wrong results (SECURITY.md §39).

---

# ADR-027 — Recorded Vector-Only Retrieval Baseline (RAG_SYSTEM.md §37 Gate)

## Context

RAG_SYSTEM.md §37 requires implementing and evaluating simple vector retrieval before adding lexical retrieval, fusion, or reranking, and requires that each later stage clear a measured improvement over this baseline before being kept. `scripts/evaluate_retrieval.py` (BACKLOG.md 4.10) was built and, once a real `GEMINI_API_KEY` was available, run live against the 5 `retrieval`-tagged questions in the canonical evaluation question bank (DATASET.md §33), with all 5 Northstar business documents ingested, chunked, and embedded through the real pipeline (Phase 4 Increments 1-6).

## Decision

Record the following as the vector-only baseline, measured live (not estimated), K=5:

| Metric | Value |
|---|---|
| Recall@5 | 1.00 (5/5) |
| Precision@5 | 0.20 |
| MRR | 1.00 |

Per-question detail: all 5 questions retrieved their expected document, ranked first (rank 1), with the `expected_fact` substring present in the matching chunk's content in all 5 cases.

## Rationale for what this means for 4.5-4.7

Recall@5 and MRR are already at their maximum possible value (1.00). No retrieval algorithm change (lexical retrieval, fusion, or reranking) can measurably improve a metric that has already reached its ceiling — there is no headroom left to demonstrate an improvement against. Precision@5 = 0.20 is not a ranking-quality artifact: the entire Northstar document corpus contains exactly 5 documents (5 chunks, one per document, at current chunk sizes), so any K=5 query mechanically retrieves every chunk in the corpus, capping precision at 1/5 regardless of ranking algorithm. This matches RAG_SYSTEM.md §37's own prediction: "the Northstar document corpus is small... lexical retrieval and reranking are not assumed to be net-positive at this corpus size."

This is exactly the outcome the evaluation gate exists to catch. Per RAG_SYSTEM.md §37, "a stage that fails its gate is removed or left disabled, not kept 'for completeness.'" BACKLOG.md 4.5-4.7 are still implemented and comparatively evaluated (not skipped outright) so the "implement → evaluate → compare" procedure is followed literally rather than assumed from this reasoning alone — but the a priori expectation, recorded here before that work begins, is that none of them will be adopted as the default active retrieval path for the Northstar-scale corpus.

## Consequences

* Vector-only retrieval (`VectorSearchService`, Increment 5) remains the active default retrieval path unless a later increment's comparative live evaluation shows a measured improvement.
* Any future increase in corpus size (more documents, more workspaces) that changes this calculus should re-run `make evaluate-retrieval` rather than assume this baseline still holds — a larger corpus removes the "precision capped by total corpus size" artifact and gives lexical/fusion/reranking real headroom to prove (or fail to prove) value.

---

# ADR-028 — Lexical Retrieval: PostgreSQL Full-Text Search

## Context

BACKLOG.md 4.5 requires selecting and recording a PostgreSQL lexical search approach before implementing it. RAG_SYSTEM.md §17 names PostgreSQL full-text search as the candidate implementation, to be benchmarked before introducing additional infrastructure (a dedicated search engine such as Elasticsearch/Typesense/Meilisearch was never seriously in scope — CLAUDE.md §3/§4 already excludes infrastructure not clearly needed, and RAG_SYSTEM.md §17 itself frames Postgres FTS as the thing to benchmark, not one option among several to weigh from scratch).

## Decision

Use PostgreSQL's built-in full-text search:

* A generated, stored `content_tsv tsvector` column on `document_chunks` (`GENERATED ALWAYS AS (to_tsvector('english', content)) STORED`) — Postgres keeps it in sync with `content` automatically; the application never writes to it.
* A GIN index on `content_tsv` for query performance.
* Query-time, `websearch_to_tsquery('english', query)` (not the lower-level `plainto_tsquery`/`to_tsquery`) — it accepts ordinary phrasing (quoted phrases, "or", "-exclude") close to how a business question is actually typed, rather than requiring tsquery's own operator syntax.
* Ranking via `ts_rank`, matching only rows where `content_tsv @@ tsquery` (non-matching rows are excluded, not merely ranked last).
* `DocumentChunkRepository.search_by_text(workspace_id, query, limit)` mirrors `search_by_embedding`'s shape (same workspace-scoping pattern, same `(DocumentChunk, score)` return shape) so both can feed a common fusion step (BACKLOG.md 4.6).

## Rationale

* No new infrastructure: Postgres is already the primary datastore (ADR-003); a generated column + GIN index adds no new service, dependency, or operational surface.
* `GENERATED ALWAYS ... STORED` removes an entire class of bugs (chunk content updated but tsvector not refreshed) by construction — there is no application code path that could let the two drift apart.
* `websearch_to_tsquery` over `plainto_tsquery`: business questions in this project (e.g. "What is the standard delivery window?") are natural sentences, and `websearch_to_tsquery` degrades gracefully on them while still supporting quoted-phrase/exclusion syntax if a caller (or a future agent tool) uses it.

## Alternatives

* **Elasticsearch/OpenSearch/Meilisearch/Typesense:** rejected — introduces a new service, new operational surface, and a second index to keep consistent with Postgres, for a corpus of 5 documents. Revisit only if a measured need at real scale emerges (CLAUDE.md §3).
* **`plainto_tsquery`/`to_tsquery` instead of `websearch_to_tsquery`:** rejected as the primary query function — `to_tsquery` requires callers to already speak tsquery's boolean operator syntax, and `plainto_tsquery` silently ANDs every word together with no phrase/exclusion support, both a worse fit for natural-language business questions than `websearch_to_tsquery`.
* **A trigger-maintained tsvector column instead of `GENERATED ALWAYS`:** rejected — Postgres 12+'s generated-column support does the same job with less code and no trigger to maintain.

## Consequences

* New Alembic migration (`f47b2e6a9c31`) adds `content_tsv` + its GIN index; no application code ever writes to `content_tsv`.
* `search_by_text`'s output feeds BACKLOG.md 4.6 (hybrid fusion) — see ADR-027 for why, at Northstar's current corpus size, this stage is not expected to change the already-at-ceiling Recall@5/MRR baseline, and Increment 8 records the actual measured comparison rather than assuming this.

---

# ADR-029 — Hybrid Fusion Strategy: Reciprocal Rank Fusion (k=60)

## Context

BACKLOG.md 4.6 requires combining vector (ADR-025) and lexical (ADR-028) retrieval into one ranked result list. RAG_SYSTEM.md §20 names Reciprocal Rank Fusion (RRF) as the initial preferred strategy and requires the exact formula/configuration to be documented during implementation.

## Decision

* **Formula:** for each retriever's ranked result list, assign `1 / (k + rank)` to each chunk (`rank` is 1-indexed); a chunk's fused score is the sum of this value across every list it appears in (0 if absent from a list).
* **k = 60** — RRF's standard/original-paper constant. Large enough that neither retriever's #1-vs-#2 ordering alone dominates the fused ranking.
* **Candidate pool:** each retriever (vector, lexical) contributes its own top `RETRIEVAL_CANDIDATE_LIMIT` (15, RAG_SYSTEM.md §19) results as fusion input; the fused list is then truncated to the caller's requested `limit`.
* **Deduplication:** by stable `chunk_id` (RAG_SYSTEM.md §21) — a chunk appearing in both retrievers' candidate lists is represented once, retaining whichever underlying `vector`/`lexical` score(s) are available on it.
* Implemented in `HybridSearchService` (`application/retrieval/hybrid_search_service.py`), composing the existing `VectorSearchService` and new `LexicalSearchService` — **not** the active default retrieval path; see the Evaluation Result section below (added once Increment 8's live comparison runs) for the keep/discard decision.

## Rationale

* RRF requires no normalization between vector cosine-similarity and lexical `ts_rank` scores, which are not on comparable scales — it only needs each list's relative ordering, which is exactly what both retrievers already produce.
* It is simple and interpretable (RAG_SYSTEM.md §20's own stated reasons), with a single tunable constant rather than a learned weighting scheme.

## Alternatives

* **Weighted linear combination of normalized scores:** rejected — requires choosing a normalization scheme for two structurally different score types (cosine similarity vs. `ts_rank`) and a weighting hyperparameter, adding tuning surface RRF avoids entirely.
* **A different `k`:** rejected — 60 is RRF's well-established default; there is no Northstar-specific evidence yet to justify a different value, and introducing one without justification would be tuning without a signal to tune against.

## Consequences

* `RetrievalResult`/`RetrievalScores` (`application/retrieval/results.py`) now carry `vector`, `lexical`, and `fusion` fields (matching RAG_SYSTEM.md §26's example schema) so any retrieval stage's output — vector-only, lexical-only, or fused — flows through one shared shape.
* The live comparison against ADR-027's vector-only baseline is recorded as an update to this ADR once `make evaluate-retrieval` is run, per RAG_SYSTEM.md §37's gate.

## Evaluation Result (RAG_SYSTEM.md §37 Gate) — Hybrid Does Not Clear the Gate

`make evaluate-retrieval` was run live (real Gemini calls) comparing `HybridSearchService` (this ADR) against the `VectorSearchService` baseline (ADR-027), same 5 `retrieval`-tagged questions, K=5:

| Metric | Vector-only | Hybrid (RRF) | Delta |
|---|---|---|---|
| Recall@5 | 1.00 | 1.00 | +0.00 |
| Precision@5 | 0.20 | 0.20 | +0.00 |
| MRR | 1.00 | 1.00 | +0.00 |

No metric improved. This confirms ADR-027's prediction exactly: Recall/MRR were already at their ceiling (1.00), leaving no headroom for any fusion strategy to improve them, and Precision@5 is capped by the 5-chunk total corpus size regardless of ranking method.

**Decision: hybrid fusion does not clear the RAG_SYSTEM.md §37 gate at Northstar's current corpus size.** Per §37, "a stage that fails its gate is removed or left disabled, not kept 'for completeness.'" `VectorSearchService` (vector-only) remains the sole active default retrieval path. `HybridSearchService`/`LexicalSearchService` remain in the codebase (tested, working) but are not wired into any default-path caller — they are available to be revisited if the corpus grows enough to give this comparison real headroom (see ADR-027's Consequences).

---

# ADR-030 — Reranker Selection: Gemini Generation, Structured Relevance Scoring

## Context

BACKLOG.md 4.7 requires selecting and recording a reranker before implementing it. RAG_SYSTEM.md §22 names three candidate approaches: a dedicated cross-encoder, a provider reranking API, or carefully constrained model-based reranking. ADR-025 already established Google Gemini as this project's model provider for embeddings.

## Decision

Use **carefully constrained Gemini-generation-based reranking**:

* Model: `gemini-flash-latest` (configurable via `RERANKER_MODEL`) — Google's rolling alias for its current fast/low-cost generation model, appropriate for a scoring task rather than open-ended generation. Using the rolling alias rather than a dated snapshot (e.g. `gemini-2.5-flash`, which stopped being available to this project partway through this phase) avoids re-breaking when Google retires a specific snapshot.
* Structured JSON output (ADR-011) via `response_schema`/`response_mime_type="application/json"`: the model returns `{"scores": [{"index": int, "relevance_score": float}, ...]}`, one entry per candidate — never free-form prose to parse.
* Input per RAG_SYSTEM.md §23: query + candidate content only (truncated to 1000 characters per candidate), no full source document, no unnecessary metadata.
* Retrieved candidate text is explicitly framed in the prompt as untrusted evidence to score, not instructions to follow (SECURITY.md §15-16, RAG_SYSTEM.md §29/§31) — consistent with how retrieved content is treated everywhere else in the system.
* Bounded retry only on transient failures (5xx, 429), same policy as `GeminiEmbeddingProvider` (ADR-025).
* Latency and token usage are logged per call (`duration_ms`, `prompt_token_count`, `candidates_token_count`) — satisfies BACKLOG.md 4.7's "track latency/cost" at the log level; persisted, queryable observability is Phase 9 scope (ARCHITECTURE.md §20).
* Implemented as `GeminiReranker` (`infrastructure/rerankers/gemini_reranker.py`) behind a narrow `Reranker` protocol (`infrastructure/rerankers/base.py`), composed with any base search service via `RerankingService` (`application/retrieval/reranking_service.py`) — mirrors the `EmbeddingProvider`/`HybridSearchService` composition pattern already established in this phase.
* Reranks on top of the vector-only baseline's candidates (not the hybrid-fused candidates), since ADR-029 already found fusion does not improve on vector-only at Northstar's scale — reranking is evaluated against the current best-performing pipeline, per RAG_SYSTEM.md §37's sequential baseline-first procedure.

## Rationale

* Reuses the already-established Gemini vendor relationship (ADR-025) rather than introducing a third AI vendor (e.g. Cohere's dedicated Rerank API) purely for this one stage, avoiding a new account, API key, and dependency for a corpus this small.
* Structured output removes the "parse the model's prose" failure mode entirely — the model cannot return an ambiguous or partially-parseable response by construction.
* A fast/cheap generation model is appropriate here: the task is bounded scoring over ≤15 short candidates, not long-form generation.

## Alternatives

* **Cohere Rerank API (dedicated reranking endpoint):** a reasonable alternative and arguably more purpose-built, but rejected for V1 — a third vendor/API key for one pipeline stage is not justified before this stage has even cleared its evaluation gate.
* **A local cross-encoder (e.g. sentence-transformers):** rejected for the same reason ADR-025 rejected a local embedding model — adds a heavy dependency (torch) to the deployed API image for a benefit not yet proven to matter at this corpus size.
* **Free-form text generation, parsed with regex/heuristics:** rejected — exactly the "unconstrained prose" pattern ADR-011 and ARCHITECTURE.md §13 warn against when application logic depends on the output shape.

## Consequences

* New core dependency surface: none (`google-genai`, already a dependency per ADR-025, also provides `generate_content`).
* The live comparison against the current best baseline (vector-only, ADR-027) is recorded as an update to this ADR once `make evaluate-retrieval` is run with reranking included, per RAG_SYSTEM.md §37's gate.

## Evaluation Result (RAG_SYSTEM.md §37 Gate) — Reranking Does Not Clear the Gate

`make evaluate-retrieval` was run live (real Gemini embedding + generation calls) comparing vector-only candidates reranked by `GeminiReranker` against the `VectorSearchService` baseline (ADR-027), same 5 `retrieval`-tagged questions, K=5:

| Metric | Vector-only | Hybrid (RRF) | +Reranking |
|---|---|---|---|
| Recall@5 | 1.00 | 1.00 | 1.00 |
| Precision@5 | 0.20 | 0.20 | 0.20 |
| MRR | 1.00 | 1.00 | 1.00 |

Identical to both the vector-only baseline and the hybrid fusion result — no metric changed. This is the same structural finding as ADR-029: Recall/MRR were already at their ceiling, and Precision@5 remains capped by the 5-chunk total corpus size, leaving no headroom for reranking (or any other stage) to demonstrate improvement.

**Decision: reranking does not clear the RAG_SYSTEM.md §37 gate at Northstar's current corpus size.** `VectorSearchService` (vector-only, no reranking) remains the sole active default retrieval path. `GeminiReranker`/`RerankingService` remain in the codebase (tested, working, verified against a real live run) but are not wired into any default-path caller — available to be revisited if a larger corpus gives this comparison real headroom (see ADR-027's Consequences, which applies identically here).

---

# ADR-031 — LLM Generation Provider: Google Gemini (`generate_structured`/`generate`)

## Context

ARCHITECTURE.md §12 requires an explicit `LLMProvider` abstraction (conceptually `generate()`/`generate_structured()`/`stream()`) so business logic never depends on one vendor (ADR-015). No such abstraction existed before Phase 5: ADR-025 selected Gemini only for embeddings, and ADR-030 uses Gemini generation narrowly inside the reranker, not as a general-purpose provider callers elsewhere can use. Phase 5 is the first place natural-language business questions must drive structured AI output (BACKLOG.md 5.2 analysis intent/plan, 5.3 SQL proposal, per ADR-011) and, separately, produce a bounded natural-language interpretation of a computed result (ANALYTICS_ENGINE.md §2/§15's "Natural-Language Interpretation" step).

## Decision

Introduce a narrow `LLMProvider` protocol (`infrastructure/llm/base.py`) with exactly two methods:

* `generate_structured(prompt, response_model) -> BaseModel` — structured JSON output validated against a caller-supplied Pydantic model, used wherever AI output drives program logic (ADR-011): analysis intent/plan (BACKLOG.md 5.2), SQL proposals (5.3).
* `generate(prompt) -> str` — bounded free-form text, used only where output is presentation prose that does not drive control flow: result interpretation (ANALYTICS_ENGINE.md §15, "the LLM may say... but all numerical values must derive from query/calculation outputs").

`stream()` is deliberately not implemented — nothing in scope through Phase 5 needs token streaming (Investigation SSE, Phase 7, streams structured *lifecycle events*, not raw LLM tokens); it is not part of this interface until a real caller needs it, matching how `EmbeddingProvider` (ADR-025) only ever implemented `embed_batch`, never the `embed_text` singular form ARCHITECTURE.md's conceptual sketch also listed.

Implementation: `GeminiLLMProvider` (`infrastructure/llm/gemini_provider.py`), reusing the already-established `google-genai` SDK/vendor relationship (ADR-025/030). `generate_structured` uses the same `response_mime_type="application/json"` + `response_schema=<pydantic model>` pattern as `GeminiReranker` (ADR-030); `generate` is a plain `generate_content` call with no schema. A `FakeLLMProvider` (`infrastructure/llm/fake_provider.py`) — a scripted queue of canned responses per call — is used by all automated tests (TESTING.md §30, mirroring `FakeEmbeddingProvider`).

New setting: `LLM_MODEL` (default `gemini-flash-latest`, the same rolling alias ADR-030 already uses for its own reasons — avoids pinning a dated snapshot that Google can retire mid-project).

## Rationale

* Reuses the existing Gemini vendor relationship and SDK rather than introducing a third AI vendor for one more capability (same reasoning ADR-025/030 already applied).
* A two-method interface (not the full three-method sketch) matches CLAUDE.md §15 ("avoid speculative abstractions") and the project's own precedent (`EmbeddingProvider`) of implementing only the subset of a conceptual interface that has a real caller.
* Keeping `generate_structured` and `generate` as separate methods (rather than one method with an optional schema) makes ADR-011's structured-vs-free-text distinction visible at every call site, not just a runtime flag.

## Alternatives

* **OpenAI or Anthropic for generation only, Gemini for embeddings:** rejected — splits the AI vendor surface in two for no benefit; ADR-025 already established Gemini generation works well for structured output (ADR-030 already relies on it).
* **A single `generate(prompt, response_model: type[BaseModel] | None = None)` method:** rejected — collapses ADR-011's structured/free-text distinction into a runtime parameter instead of the call site itself, making it harder to audit "does this AI output drive program logic" by reading signatures alone.

## Consequences

* `apps/api/pyproject.toml`/`.env.example` gain no new dependency (`google-genai` already present per ADR-025) beyond the new `LLM_MODEL` setting.
* Any future Phase 6 agent orchestration reasoning call is expected to reuse this same `LLMProvider`, not introduce a second one, unless a concrete need (e.g. streaming) forces `stream()` to be added then.

---

# ADR-032 — SQL AST Parsing (`sqlglot`) and Read-Only Analytics Execution via `SET LOCAL ROLE`

## Context

BACKLOG.md 5.4/5.5 require an AST-based SQL validator (SECURITY.md §11: "prefer parsing SQL into an AST... rather than regex-only checks") and a restricted read-only database role for AI-generated analytical SQL (ADR-008, SECURITY.md §8/§12). Two concrete choices were needed: which SQL parsing library to use, and how the "restricted role" requirement is actually wired into query execution without inventing a second database credential/secret.

## Decision

**SQL parsing/validation:** use [`sqlglot`](https://github.com/tobymao/sqlglot), a pure-Python, dependency-free SQL parser supporting the Postgres dialect. Used for two distinct, separately-testable passes:

1. **Identifier resolution** (`infrastructure/analytics/sql_resolver.py`): the LLM is shown only display names (ANALYTICS_ENGINE.md §5); after generation, `sqlglot` rewrites every `Table`/`Column` AST node whose name matches a known display name in the requesting workspace's catalog to its corresponding `analytics.<physical_table_name>`/`<physical_name>` identifier (ADR-017). Any identifier that does not resolve raises `SqlResolutionError` — the query is never executed with a partially-resolved or literal display name.
2. **Validation** (`infrastructure/analytics/sql_validator.py`), run only on the already-resolved (physical-identifier) SQL: exactly one statement (reject `;`-stacked statements, SECURITY.md §12), root statement must be `SELECT`/`WITH ... SELECT` (SECURITY.md §10), every referenced table must be in the dynamically-built, workspace-scoped physical-table allowlist (ADR-017) and the `analytics` schema (never `app`, SECURITY.md §13), a small denylist of resource-exhaustion/file/network functions is rejected (e.g. `pg_sleep`, `dblink`, `pg_read_file`, `lo_import`, `copy_from_program`), and a `LIMIT` is enforced by rewriting the AST (capping any existing `LIMIT` to the configured maximum, or adding one if absent) rather than trusting the LLM to have added one (SECURITY.md §14).

**Read-only execution role:** a `NOLOGIN` Postgres role (`opspilot_analytics_ro`) is created by migration, granted `USAGE` on the `analytics` schema and `SELECT` on all its tables (present and future, via `ALTER DEFAULT PRIVILEGES`), with no privileges on `app` whatsoever. The role has no password and is never a second connection credential/secret. Instead, `AnalyticsQueryExecutor` opens a **dedicated connection** (never the ambient per-request `AsyncSession` used elsewhere — see Rationale), begins an explicit transaction, runs `SET LOCAL ROLE opspilot_analytics_ro` + `SET LOCAL statement_timeout`, executes the validated query, and always rolls back (read-only, so commit vs. rollback is semantically equivalent, and rollback guarantees the connection returns to the pool with the role/timeout fully unset for the next borrower).

## Rationale

* `sqlglot` needs no database connection or native extension (pure Python), matches SECURITY.md §11's explicit ask for AST-based (not regex) validation, and is mature enough to support two independent passes (rename, then validate) over the same grammar without a second parser.
* Splitting "resolve display→physical" from "validate" into two passes over two different SQL strings (LLM's display-name SQL, then the fully-physical SQL) keeps each pass's job small and independently testable — resolution failures (unknown identifier) and validation failures (disallowed statement/table/function) are distinguishable error states, which matters for ANALYTICS_ENGINE.md §28's bounded-retry-with-feedback flow.
* `SET LOCAL ROLE` on a dedicated connection avoids provisioning, securing, and rotating a second database credential (a new secret per SECURITY.md §7) for a role that never needs its own login. Reusing the ambient request-scoped `AsyncSession` (as `table_builder.py` does for ingestion DDL) was considered and rejected specifically because `SET LOCAL` only reverts at transaction end — the ambient session's transaction spans the whole HTTP request, so any later query on that same session after an analytics call would silently keep running as the restricted role (or, worse, the restriction would leak backwards if ordering ever changed). A dedicated connection with an explicit, always-rolled-back transaction has no such leakage window.
* Even if SQL validation had a bug that let a disallowed statement or table through, the role's Postgres-enforced privileges (SELECT-only, `analytics`-only) independently block it — true defense in depth (SECURITY.md's "multiple layers" principle), not reliance on the validator alone.

## Alternatives

* **A second database credential/connection string for a login-capable read-only role:** rejected — a real login role needs a password (a new secret, SECURITY.md §7) and a second pool to manage, for no capability `SET LOCAL ROLE` on a `NOLOGIN` role doesn't already provide.
* **Regex-based SQL validation:** rejected outright by SECURITY.md §11 itself.
* **`pglast` (libpg_query bindings) instead of `sqlglot`:** a reasonable alternative that parses actual Postgres grammar via the real Postgres parser; not selected because it requires a compiled C extension (heavier dependency footprint) where `sqlglot`'s pure-Python Postgres dialect support is sufficient for this project's validation needs (single-statement, table/function-name-level checks — not exhaustive Postgres grammar coverage).
* **Skipping identifier resolution and letting the LLM see physical identifiers directly:** rejected — ANALYTICS_ENGINE.md §5 explicitly settles this: "the LLM only ever sees the display names... SQL generation resolves them to physical identifiers."

## Consequences

* `apps/api/pyproject.toml` gains `sqlglot` as a core dependency.
* New Alembic migration creates `opspilot_analytics_ro` and grants role membership to the application's own connecting user via `GRANT opspilot_analytics_ro TO CURRENT_USER`, so the migration does not need to know the configured `POSTGRES_USER` value literally.
* Any future analytical execution path (Phase 6 agent, Phase 10 evaluation) must go through `AnalyticsQueryExecutor`, never open its own ad hoc connection to run AI-influenced SQL — this is the single enforced choke point the role/timeout/rollback guarantees apply to.
