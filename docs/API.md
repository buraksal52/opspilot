# OpsPilot — API Specification

## 1. Purpose

This document defines the initial HTTP API boundaries for OpsPilot.

The API should remain:

* predictable,
* versioned,
* typed,
* resource-oriented where appropriate.

Initial base path:

```text
/api/v1
```

Exact request and response schemas may evolve during implementation.

---

# 2. General API Principles

Use JSON for normal request and response bodies.

Use multipart/form-data for file uploads.

Use consistent error structures.

Avoid exposing internal database models directly.

Public API schemas should remain separate from persistence schemas where useful.

---

# 3. Standard Error Response

Recommended shape:

```json
{
  "error": {
    "code": "DATA_SOURCE_NOT_FOUND",
    "message": "The requested data source does not exist.",
    "details": {}
  }
}
```

Do not return raw stack traces to clients.

---

# 4. Health

## GET `/api/v1/health`

Purpose:

Verify API availability.

### Response

```json
{
  "status": "ok"
}
```

---

# 5. Workspaces

## GET `/api/v1/workspaces`

Return available workspaces for the current user.

---

## POST `/api/v1/workspaces`

Create a workspace.

### Request

```json
{
  "name": "Northstar Commerce"
}
```

### Response

```json
{
  "id": "uuid",
  "name": "Northstar Commerce",
  "slug": "northstar-commerce"
}
```

---

## GET `/api/v1/workspaces/{workspace_id}`

Return workspace details.

---

# 6. Data Sources

## GET `/api/v1/workspaces/{workspace_id}/data-sources`

Return uploaded data sources.

### Optional filters

```text
status
source_type
```

---

## POST `/api/v1/workspaces/{workspace_id}/data-sources/upload`

Upload a supported source.

### Content Type

```text
multipart/form-data
```

### Supported Initial Types

* CSV
* PDF
* Markdown
* plain text

### Response

```json
{
  "id": "uuid",
  "name": "orders.csv",
  "source_type": "CSV",
  "status": "UPLOADED"
}
```

Processing may continue asynchronously.

---

## GET `/api/v1/data-sources/{data_source_id}`

Return metadata and processing state.

---

## DELETE `/api/v1/data-sources/{data_source_id}`

Delete or soft-delete a data source.

Its Document/Dataset and derived chunks/embeddings/physical analytics table must no longer be available to *new* retrieval, analysis, or investigations.

Evidence already created by *past* investigations is unaffected: it holds a bounded snapshot captured at creation time (DATA_MODEL.md §15) and remains inspectable. The source itself is shown as unavailable in that historical context, but the evidence content is not deleted or hidden.

---

# 7. Documents

## GET `/api/v1/workspaces/{workspace_id}/documents`

Return available processed documents.

---

## GET `/api/v1/documents/{document_id}`

Return document metadata.

Do not automatically return the entire document body if unnecessarily large.

---

## GET `/api/v1/documents/{document_id}/chunks`

Development/debug endpoint.

Returns chunks for inspection.

This endpoint may be restricted in future production environments.

---

# 8. Datasets

## GET `/api/v1/workspaces/{workspace_id}/datasets`

Return structured datasets.

---

## GET `/api/v1/datasets/{dataset_id}`

Return:

* name
* status
* row count
* column count
* inferred schema
* profile statistics

---

## GET `/api/v1/datasets/{dataset_id}/preview`

Return a bounded row preview.

Example:

```json
{
  "columns": ["order_id", "order_date", "total_amount"],
  "rows": [],
  "limit": 50
}
```

Always enforce a server-side maximum.

---

# 9. Investigations

## POST `/api/v1/workspaces/{workspace_id}/investigations`

Start an investigation.

### Request

```json
{
  "query": "Why did refunds increase this month?"
}
```

### Response

```json
{
  "id": "uuid",
  "status": "CREATED",
  "query": "Why did refunds increase this month?"
}
```

Long-running processing should not block the request unnecessarily.

---

## GET `/api/v1/investigations/{investigation_id}`

Return investigation summary and current state.

Example:

```json
{
  "id": "uuid",
  "query": "Why did refunds increase this month?",
  "status": "RUNNING",
  "summary": null,
  "started_at": "...",
  "completed_at": null
}
```

---

## GET `/api/v1/workspaces/{workspace_id}/investigations`

Return investigation history.

Possible filters:

```text
status
created_after
created_before
```

---

## POST `/api/v1/investigations/{investigation_id}/cancel`

Request investigation cancellation.

Cancellation support may initially be best-effort.

---

# 10. Investigation Steps

## GET `/api/v1/investigations/{investigation_id}/steps`

Return ordered investigation steps.

Example:

```json
[
  {
    "sequence_number": 1,
    "title": "Analyze refund trend",
    "status": "COMPLETED"
  }
]
```

---

# 11. Tool Executions

## GET `/api/v1/investigations/{investigation_id}/tool-executions`

Return tool traces.

This is primarily an observability/debugging API.

Sensitive tool input/output must be filtered where necessary.

---

# 12. Evidence

## GET `/api/v1/investigations/{investigation_id}/evidence`

Return investigation evidence.

Example:

```json
[
  {
    "id": "uuid",
    "evidence_type": "METRIC",
    "title": "Refund rate increase",
    "content": "Refund rate increased from 4.1% to 5.2%.",
    "source_reference": {}
  }
]
```

---

## GET `/api/v1/evidence/{evidence_id}`

Return evidence details.

Document evidence may include:

* document name
* page
* source excerpt

Query evidence may include:

* SQL
* bounded result preview
* dataset references

---

# 13. Investigation Result

## GET `/api/v1/investigations/{investigation_id}/result`

Return the final structured result.

Example conceptual response:

```json
{
  "summary": "Refunds increased primarily because of shipping delays.",
  "findings": [
    {
      "statement": "Late-delivery refunds increased after July 11.",
      "evidence_ids": ["uuid"]
    }
  ],
  "recommendations": [
    {
      "title": "Review RapidShip SLA",
      "description": "..."
    }
  ],
  "charts": [],
  "confidence": {
    "overall": 0.86
  }
}
```

Exact schema should be finalized with AGENT_SYSTEM.md.

---

# 14. Investigation Events

## GET `/api/v1/investigations/{investigation_id}/events`

Transport:

```text
text/event-stream
```

Used for SSE.

Possible event types:

```text
investigation.started
plan.created
step.started
step.completed
tool.started
tool.completed
evidence.added
investigation.synthesizing
investigation.completed
investigation.failed
```

Example SSE payload:

```text
event: step.started
data: {"step_id":"uuid","title":"Analyze refund trends"}
```

---

# 15. Retrieval Debugging

Development-only or restricted endpoints may be introduced.

Example:

## POST `/api/v1/debug/retrieval`

### Request

```json
{
  "workspace_id": "uuid",
  "query": "What is the standard delivery window?"
}
```

### Response

May contain:

* lexical candidates
* vector candidates
* fusion scores
* reranker scores
* selected chunks

This should not necessarily be public in production.

---

# 16. Analytics Debugging

Potential restricted endpoint:

## POST `/api/v1/debug/analytics`

Used to inspect:

* selected datasets
* generated SQL
* validation result
* query result

Must use the same safe execution path as normal investigations.

Do not create an unsafe debug bypass.

---

# 17. Evaluation

## POST `/api/v1/evaluations`

Start an evaluation run.

This may initially remain internal/development-only.

---

## GET `/api/v1/evaluations/{evaluation_id}`

Return evaluation progress and results.

---

# 18. Pagination

List endpoints should eventually support:

```text
limit
cursor
```

Avoid deep offset pagination for large resources.

For V1, simple bounded pagination is sufficient.

---

# 19. Authentication

Per ADR-019, authenticated requests use a JWT bearer access token:

```text
Authorization: Bearer <token>
```

Tokens are issued via an email/password login endpoint (e.g. `POST /api/v1/auth/login`) and verified using PyJWT. There is no server-side session store; tokens are stateless and self-contained.

Do not tightly couple domain logic to the authentication mechanism — token issuance/verification is an infrastructure-layer concern (ARCHITECTURE.md §6).

---

# 20. Authorization

All workspace-owned resources must enforce workspace access.

A user must not access another workspace's:

* documents
* datasets
* investigations
* evidence

even if they know a resource UUID.

---

# 21. Idempotency

Potentially repeatable operations should be evaluated for idempotency.

Examples:

* data processing
* background jobs
* embedding generation

Duplicate processing must not create uncontrolled duplicate records.

---

# 22. File Upload Security

Upload endpoints must enforce:

* maximum file size
* supported MIME/type validation
* filename sanitization
* parser error handling

Do not trust file extensions alone.

---

# 23. API Stability

During early development API schemas may evolve.

Once frontend dependencies stabilize, avoid unnecessary breaking changes.

Major contract changes should update this document.
