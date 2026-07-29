# OpsPilot — Testing and Evaluation Strategy

## 1. Purpose

OpsPilot contains both deterministic software components and probabilistic AI components.

Testing must treat them differently.

A normal unit test suite alone is not sufficient for an AI system.

The overall quality strategy includes:

* unit tests
* integration tests
* API tests
* end-to-end tests
* AI evaluation
* deterministic dataset validation
* security tests

---

# 2. Testing Principle

Use deterministic tests whenever a deterministic answer exists.

Do not use LLM-based evaluation for problems that can be verified directly.

Example:

Refund rate calculation should be tested numerically.

Do not ask an LLM whether the refund rate "looks correct."

---

# 3. Test Structure

Suggested organization:

```text
tests/
├── unit/
├── integration/
├── api/
├── e2e/
└── evaluation/
```

Exact layout may evolve.

---

# 4. Unit Tests

Unit tests cover isolated deterministic components.

Priority areas:

* parsers
* data validators
* chunking
* schema inference
* SQL validation
* metric calculations
* tool input validation
* tool output parsing
* evidence mapping
* result transformations

---

# 5. SQL Safety Tests

SQL validation requires strong test coverage.

Must reject:

```sql
DELETE FROM orders;
```

```sql
DROP TABLE customers;
```

```sql
UPDATE orders SET total_amount = 0;
```

```sql
SELECT * FROM orders; DROP TABLE orders;
```

Must verify:

* only allowed query types
* allowed schema/table access
* query timeout behavior
* row limits
* invalid syntax handling

---

# 6. Data Ingestion Tests

Test:

* supported CSV
* malformed CSV
* supported PDF
* unsupported file type
* empty file
* oversized file
* parser failure
* duplicate upload behavior
* failed processing state

---

# 7. Dataset Integrity Tests

Northstar generation should have deterministic validation.

Verify:

* all foreign-key-style relationships are valid
* no unintended orphan refunds
* RapidShip traffic begins around migration date
* target incident patterns exist
* row counts are within expected ranges

---

# 8. Retrieval Unit/Integration Tests

Test components independently.

## Chunking

Verify:

* no content loss where avoidable
* metadata preservation
* deterministic behavior
* page references remain valid

## Vector Search

Verify relevant chunks are retrievable for known queries.

## Keyword Search

Verify exact business terminology can be recovered.

## Hybrid Search

Verify fusion does not lose critical high-quality candidates.

## Reranking

Verify expected relevant chunks are promoted for known evaluation cases.

---

# 9. Retrieval Evaluation Dataset

Uses the `retrieval`-tagged questions from the canonical evaluation question bank (DATASET.md §33), not a separately authored query list.

Example:

```json
{
  "query": "What is the standard delivery window?",
  "expected_document": "Shipping Policy",
  "expected_pages": [1, 2]
}
```

Evaluation should track relevant chunks/documents.

---

# 10. Retrieval Metrics

Potential metrics:

## Recall@K

Did the expected relevant evidence appear in the top K?

## Precision@K

How much of the retrieved top K is actually relevant?

## MRR

How highly ranked was the first relevant result?

Exact thresholds should be established after a baseline exists.

---

# 11. Analytics Tests

All important analytical calculations should have known expected values.

Examples:

* refund rate
* average delivery time
* ticket volume
* revenue impact
* provider comparison

Whenever possible, compare against manually computed or trusted deterministic reference values.

---

# 12. Generated SQL Tests

Use known questions and verify important properties.

Example:

Question:

> Compare refund rates before and after July 11.

Check:

* correct tables selected
* appropriate date boundary
* correct aggregation
* SQL passes validator
* numerical result matches expected value

Do not require exact SQL string equality if several valid SQL queries exist.

Test semantics/results instead.

---

# 13. Tool Contract Tests

Every tool should have tests for:

* valid input
* invalid input
* expected output schema
* backend failure
* timeout
* permission violation

The agent must receive predictable tool responses.

---

# 14. Agent Tests

Agent behavior is probabilistic.

Avoid overly brittle exact-string tests.

Test important invariants.

Examples:

Given:

> Why did refunds increase?

A successful investigation should:

* use structured analytics
* identify refund increase
* examine delivery/shipping evidence
* produce at least one valid supporting evidence item
* not invent unsupported numerical claims

---

# 15. Agent Failure Tests

Test scenarios such as:

* no relevant documents
* dataset missing
* SQL generation failure
* retrieval service failure
* LLM timeout
* tool returns empty result
* contradictory evidence

The system should fail clearly rather than fabricate certainty.

---

# 16. Evidence Tests

Verify:

* claims reference existing evidence
* evidence belongs to the same workspace
* source references resolve
* document page references are valid
* metric values match deterministic computation
* evidence is not fabricated after generation

---

# 17. End-to-End Tests

Core E2E path:

```text
Create workspace
→ upload Northstar data
→ process sources
→ ask investigation question
→ wait for completion
→ inspect result
→ inspect evidence
```

The primary E2E investigation:

> Why did refunds increase this month?

---

# 18. Primary Demo Acceptance Test

This is the primary `agent`/`e2e`-tagged question from the canonical evaluation question bank (DATASET.md §33).

Expected broad conclusion:

Refunds increased substantially due to shipping delays associated with the July 11 RapidShip migration.

The test should not require identical prose.

It should verify:

* refund increase detected
* July 11 period identified
* shipping delays detected
* RapidShip relationship identified
* supporting evidence exists

---

# 19. Secondary E2E Questions

Maintain at least five reliable investigations, drawn from the `agent`/`e2e`-tagged questions in the canonical evaluation question bank (DATASET.md §33).

Examples:

1. Why did refunds increase this month?
2. Which customer segment was most affected?
3. What changed around July 11?
4. Which provider had worse delivery performance?
5. Which products had the highest refund rate?

---

# 20. AI Generation Evaluation

Evaluate final output on dimensions such as:

* groundedness
* factual correctness
* evidence support
* numerical correctness
* relevance
* usefulness

Do not rely exclusively on LLM-as-a-judge.

Use deterministic checks wherever possible.

---

# 21. Groundedness

A major claim is grounded if sufficient supporting evidence exists.

Example:

Claim:

> RapidShip deliveries averaged 4.6 days.

Groundedness requires:

* relevant analytical evidence,
* matching calculated value.

An LLM citation to unrelated text is not sufficient.

---

# 22. Citation Correctness

Citation evaluation should answer:

1. Does the cited source exist?
2. Does it support the claim?
3. Does referenced metadata resolve correctly?
4. Is the claim stronger than the source permits?

---

# 23. Confidence Testing

If confidence scoring is introduced, it must not be based solely on LLM self-report.

Test that confidence responds meaningfully to:

* evidence availability
* source agreement
* analytical support
* retrieval quality

A weak-evidence scenario should not produce consistently high confidence.

---

# 24. Observability Tests

Ensure execution traces capture required events.

Examples:

* investigation start
* step start/end
* tool call
* failure
* completion

Verify failures preserve useful debugging information.

---

# 25. SSE Tests

Test:

* event ordering
* connection termination
* investigation completion
* failure events
* reconnect behavior if supported

---

# 26. API Tests

Test:

* validation errors
* authorization
* missing resources
* invalid workspace access
* successful uploads
* investigation creation
* result retrieval

Use the actual FastAPI application where practical.

---

# 27. Security Tests

Priority areas:

## SQL Injection

Generated and user-influenced SQL must remain restricted.

## Prompt Injection

Uploaded documents may contain text such as:

> Ignore all previous instructions.

This must be treated as document content, not application instruction.

## File Upload

Test malformed and unsupported files.

## Cross-Workspace Access

Resource IDs must not bypass workspace authorization.

---

# 28. Regression Suite

Any bug that affects core behavior should receive a regression test when practical.

Example:

If reranking once drops the correct shipping-policy chunk, add a test preventing recurrence.

---

# 29. Test Data

Prefer small deterministic fixtures for unit/integration tests.

Use the larger Northstar dataset for:

* E2E
* evaluation
* demo validation

Do not make every test depend on the full synthetic dataset.

---

# 29a. Backend Test Infrastructure (Postgres/Redis)

Per ADR-022, `tests/api` and `tests/integration` never run against the `docker compose` development stack. `make test-api` starts short-lived, dedicated containers (`opspilot-test-pg` on port `55432`, `opspilot-test-redis` on port `63790`), runs the real Alembic migration chain against them, runs the suite, then tears the containers down — regardless of test outcome.

This matters because the test session fixture runs `alembic downgrade base` at teardown, which drops the `app`/`analytics` schemas; pointed at a developer's persistent dev database, that would destroy local data. Running `pytest tests/` directly requires a matching Postgres/Redis already reachable at those ports (or `TEST_DATABASE_URL`/`REDIS_URL` overridden) — `make test-api` is the supported entry point.

---

# 30. External AI API Tests

Normal CI should not depend heavily on live paid LLM APIs.

Use:

* mocks for basic contract tests,
* recorded or controlled fixtures where appropriate,
* limited explicit live-model evaluation runs.

Do not pretend mocks validate model quality.

---

# 31. Evaluation Modes

Consider two separate modes.

## Fast Evaluation

Runs frequently.

Includes:

* deterministic tests
* retrieval metrics
* core analytics validation

## Full Evaluation

Runs manually or before major milestones.

Includes:

* live model calls
* full investigations
* groundedness evaluation
* cost and latency metrics

---

# 32. Performance Testing

Initial targets should focus on demo quality rather than massive scale.

Measure:

* ingestion latency
* retrieval latency
* SQL latency
* investigation latency
* LLM latency
* token usage

Primary demo investigation target:

Approximately:

```text
< 15–20 seconds
```

under normal demo conditions.

This target may be adjusted based on measured quality/latency tradeoffs.

---

# 33. Cost Testing

Track estimated model cost per investigation.

Evaluation runs should report:

* total LLM calls
* input tokens
* output tokens
* estimated cost

Unexpected cost regressions should be visible.

---

# 34. Definition of Tested

A feature should not be considered adequately tested unless:

* deterministic logic has deterministic tests,
* important failure paths are covered,
* integration boundaries have been exercised,
* AI behavior has appropriate evaluation where needed.

---

# 35. Phase Quality Gates

Before moving from a major technical phase, verify the relevant gate.

## Ingestion Gate

Northstar data loads reliably.

## RAG Gate

Known document questions retrieve correct evidence.

## Analytics Gate

Known numerical questions match ground truth.

## Agent Gate

Multi-source investigation works without hardcoded answers.

## Portfolio Gate

Primary demo is repeatable, inspectable, and technically defensible.
