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
