# OpsPilot — Product Requirements

## 1. Product Summary

OpsPilot is an AI-native Business Intelligence and Operations platform that helps users understand what is happening in their business, investigate why it is happening, and decide what should be done next.

Traditional BI tools primarily answer:

> What happened?

OpsPilot aims to additionally answer:

> Why did it happen?

> What should we do?

And in future authorized workflows:

> Do it.

OpsPilot combines:

* structured business data,
* internal documents,
* customer feedback,
* AI reasoning,
* deterministic analytics,
* evidence retrieval,
* tool execution.

---

# 2. Product Vision

Business users should not need to manually inspect multiple dashboards, spreadsheets, support tickets and internal documents to investigate an operational problem.

They should be able to ask:

> Why did refunds increase this month?

OpsPilot should perform an investigation across relevant sources and return an evidence-backed answer.

The long-term vision is:

Business Intelligence
→ Business Investigation
→ Decision Support
→ Operational Action

---

# 3. Core Product Promise

OpsPilot should help users move from:

Data

to:

Understanding

to:

Decision

to:

Action

while preserving traceability.

---

# 4. Primary User

The initial target persona is a person responsible for understanding business operations.

Examples:

* startup founder
* operations manager
* product manager
* business analyst
* customer operations manager
* e-commerce manager

The first version is not designed for specialist data scientists.

The product should allow technically non-specialist users to ask meaningful business questions.

---

# 5. Primary Job To Be Done

When an important business metric changes or an operational issue appears, I want to investigate relevant company data and documents so that I can understand the likely causes and decide what action to take.

---

# 6. Core User Journey

## Step 1 — Add Data

The user provides business data.

Initial supported sources:

* CSV
* PDF
* Markdown
* plain text

Examples:

* orders.csv
* refunds.csv
* customers.csv
* support_tickets.csv
* Shipping Policy.pdf
* Refund Policy.pdf

---

## Step 2 — Ask a Business Question

Example:

> Why did refunds increase this month?

---

## Step 3 — Investigation Planning

OpsPilot determines what information is required.

Example plan:

1. measure refund trend,
2. identify when the increase began,
3. find affected customer/order segments,
4. analyze support tickets,
5. search internal operational documents,
6. identify correlated business events,
7. estimate financial impact.

---

## Step 4 — Tool Execution

OpsPilot uses appropriate tools.

Possible tools:

* structured data query
* metric calculation
* document retrieval
* customer feedback analysis
* anomaly detection
* chart generation

---

## Step 5 — Evidence Collection

OpsPilot records evidence supporting important findings.

Example:

Finding:

> Shipping complaints increased after July 11.

Evidence:

* support_tickets.csv aggregation
* shipping incident document
* order delivery-time analysis

---

## Step 6 — Explanation

The user receives a concise investigation summary.

Example:

> Refund requests rose primarily because of delivery delays following the July 11 shipping-provider migration.

---

## Step 7 — Recommendations

OpsPilot suggests actionable next steps.

Example:

* investigate the new provider's SLA,
* proactively notify delayed customers,
* monitor refund rates for affected orders,
* introduce delayed-order alerts.

---

# 7. Product Layers

OpsPilot consists conceptually of three layers.

## Layer 1 — Business Intelligence

Answers:

> What is happening?

Capabilities:

* metrics
* trends
* comparisons
* charts
* anomaly detection
* segmentation

---

## Layer 2 — AI Business Analyst

Answers:

> Why is it happening?

Capabilities:

* investigation planning
* document retrieval
* structured data analysis
* customer feedback analysis
* evidence synthesis
* root-cause hypothesis generation

---

## Layer 3 — Operations Agent

Answers:

> What should we do?

and eventually:

> Execute the approved action.

Initial version focuses primarily on recommendations.

Operational execution should be introduced carefully and only through explicit, permission-controlled tools.

---

# 8. Primary Demo Environment

The initial product will include a fictional company:

## Northstar Commerce

Northstar Commerce is an e-commerce company with structured and unstructured operational data.

Demo data should include:

* customers
* orders
* products
* refunds
* support tickets
* operational policies
* incident reports

The dataset must contain realistic business relationships.

It must not exist merely to generate random charts.

---

# 9. Primary Demo Investigation

Main question:

> Why did refunds increase this month?

The intended hidden business event is:

A shipping provider change occurred around July 11.

Expected downstream effects include:

* longer delivery times,
* increased shipping complaints,
* increased refund requests,
* lower customer ratings,
* reduced repeat purchase behavior.

OpsPilot must discover these relationships through actual analysis.

The conclusion must not be hardcoded.

---

# 10. Additional Demo Questions

OpsPilot should eventually handle questions such as:

> When did refund behavior begin to change?

> Which customer segment is most affected?

> Which products have the highest refund rate?

> What changed around July 11?

> What is the estimated revenue impact?

> Are support complaints correlated with delivery delays?

> What internal policies are relevant?

> Which customers may be at higher churn risk?

> What actions should we take next?

---

# 11. Core Functional Requirements

## Data Management

Users should be able to:

* upload supported files,
* inspect uploaded data sources,
* see processing status,
* remove data sources,
* inspect basic metadata.

---

## Document Intelligence

OpsPilot should:

* parse documents,
* preserve useful metadata,
* chunk documents,
* generate embeddings,
* retrieve relevant content,
* return source references.

---

## Structured Analytics

OpsPilot should:

* inspect dataset schemas,
* select relevant datasets,
* generate safe analytical queries,
* execute read-only queries,
* compute deterministic metrics,
* return structured results.

---

## Investigation Engine

OpsPilot should:

* accept natural-language business questions,
* construct an investigation plan,
* execute tools,
* record investigation steps,
* collect evidence,
* generate conclusions,
* provide recommendations.

---

## Evidence

Users should be able to inspect why OpsPilot made an important claim.

Evidence should be connected to:

* source documents,
* database results,
* calculations,
* analytical outputs.

---

## Investigation History

Users should be able to revisit previous investigations.

Each investigation should preserve:

* original question,
* status,
* plan,
* steps,
* tool executions,
* evidence,
* final answer,
* timing information.

---

## Observability

OpsPilot should expose useful execution information such as:

* investigation duration,
* models used,
* tool calls,
* failures,
* token usage,
* estimated AI cost,
* retrieved context.

---

# 12. Non-Functional Requirements

## Reliability

Demo investigations should produce stable, defensible conclusions.

The same question should not generate materially contradictory answers without changes in underlying data.

---

## Explainability

Important business claims should be traceable to evidence.

---

## Safety

LLMs must not have unrestricted access to databases or external systems.

---

## Maintainability

The system should remain understandable and modular.

---

## Performance

The primary demo investigation should ideally complete within approximately 15–20 seconds under normal local/demo conditions.

This is a target rather than a hard guarantee during early development.

---

# 13. V1 Scope

V1 includes:

* local/demo authentication or simple account structure
* workspace concept
* CSV upload
* PDF upload
* document ingestion
* structured dataset ingestion
* PostgreSQL
* pgvector
* retrieval
* hybrid search
* reranking
* safe analytics
* investigation agent
* evidence tracking
* investigation UI
* charts
* execution tracing
* basic evaluation

---

# 14. Explicitly Out of Scope for V1

The following are not required:

* billing
* subscriptions
* production multi-tenancy complexity
* enterprise authentication
* Slack
* Gmail
* Notion
* Google Drive
* Shopify
* Stripe
* Kubernetes
* mobile application
* enterprise-scale distributed infrastructure
* autonomous external actions
* complex multi-agent swarms

These may be future extensions.

---

# 15. Product Principles

## Evidence Over Eloquence

A plain answer supported by strong evidence is better than an impressive unsupported answer.

---

## Tools Over Hallucination

When information can be calculated or retrieved, use a tool instead of asking the LLM to guess.

---

## Investigation Over Chat

OpsPilot should feel like a system performing work, not merely a conversation interface.

---

## Human Visibility

Users should be able to understand what the system is doing.

---

## Controlled Autonomy

AI may decide how to investigate, but permissions and side effects remain controlled by the application.

---

## Quality Over Feature Count

A smaller number of reliable capabilities is preferable to many shallow integrations.

---

# 16. Success Criteria

The initial portfolio-quality version is successful when:

1. Northstar Commerce data can be ingested.
2. Documents can be retrieved with useful source references.
3. Structured data can be analyzed safely.
4. OpsPilot can create and execute investigation plans.
5. At least five predefined business investigations work reliably.
6. Major conclusions include inspectable evidence.
7. Investigation progress can be viewed in the UI.
8. Execution information can be inspected.
9. Retrieval and answer quality have basic evaluation coverage.
10. No demo answer depends on hardcoded conclusions.

---

# 17. Portfolio Objective

OpsPilot should demonstrate competence in:

* AI engineering
* RAG
* agentic workflows
* tool calling
* backend engineering
* data analysis
* PostgreSQL
* vector search
* observability
* evaluation
* full-stack product development

The project should remain technically defensible in an interview.

The developer should be able to explain why major components exist and how they work.
