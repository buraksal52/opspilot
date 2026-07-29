OpsPilot — Analytics Engine Specification
1. Purpose

The Analytics Engine enables OpsPilot to answer quantitative business questions using structured datasets.

Its responsibility is to transform:

Natural-language analytical intent

into:

Verified deterministic computation.

The LLM may plan or explain an analysis.

It must not invent numerical results.

2. Core Workflow
Business Question
↓
Dataset Discovery
↓
Schema Context
↓
Analysis Intent
↓
Analysis Plan
↓
SQL Proposal
↓
SQL Validation
↓
Read-Only Execution
↓
Result Validation
↓
Metric / Finding
↓
Natural-Language Interpretation
3. Example

Question:

Did refunds increase after July 11?

Expected process:

identify orders/refunds datasets,
establish comparison periods,
determine refund-rate calculation,
generate SQL,
validate SQL,
execute query,
calculate/return deterministic result,
explain the comparison.
4. Main Responsibilities

The analytics module should provide:

dataset catalog,
schema inspection,
relationship awareness,
analytical planning,
safe SQL generation,
SQL validation,
query execution,
result normalization,
deterministic metric tools,
chart-ready outputs.
5. Dataset Catalog

The agent should not receive the entire database schema blindly.

Provide a controlled catalog describing:

dataset names,
descriptions,
columns,
types,
selected profile information,
known relationships.

Per ADR-017, this catalog is built dynamically per request, scoped to the requesting workspace's own Dataset records. It is never a fixed global list of table names. Each catalog entry maps a workspace's display name (`Dataset.name`, e.g. "orders") and display column names to the underlying generated physical table/columns (`Dataset.physical_table_name`, `schema_definition[...].physical_name`) — the LLM only ever sees the display names shown below; SQL generation resolves them to physical identifiers.

Example (display names, as the LLM sees them):

orders
- order_id
- customer_id
- product_id
- order_date
- shipping_provider
- delivery_days
- total_amount

refunds
- refund_id
- order_id
- refund_reason
- refund_amount
6. Dataset Selection

Given a question, first determine which datasets are relevant.

Example:

Which provider had worse delivery performance?

Relevant:

orders

Potentially irrelevant:

products
refunds

Avoid injecting unnecessary schema context.

7. Relationship Awareness

Initial Northstar relationships include:

orders.customer_id → customers.customer_id
orders.product_id → products.product_id
refunds.order_id → orders.order_id
support_tickets.order_id → orders.order_id

These should be made available to analysis planning.

Do not require the LLM to infer joins from column names every time.

8. Analytical Intent Schema

Where useful, represent analytics intent structurally.

Example:

{
  "question_type": "comparison",
  "metrics": ["refund_rate"],
  "dimensions": ["period"],
  "filters": [],
  "datasets": ["orders", "refunds"]
}

The exact schema should remain minimal.

9. Analysis Plan

Before SQL generation, complex questions should produce a brief structured plan.

Example:

1. Count delivered orders before July 11.
2. Count refunded orders before July 11.
3. Compute refund rate.
4. Repeat after July 11.
5. Compare rates.

This improves inspectability and validation.

10. SQL Generation

SQL generation receives:

user question,
selected datasets,
schema,
relationships,
analysis plan,
SQL restrictions.

It should not receive database credentials.

11. SQL Validation

Every generated query must pass validation before execution.

Required checks:

one analytical statement,
SELECT/read-only operation,
permitted schemas only,
permitted tables only,
no DDL/DML,
bounded output,
timeout,
safe functions.

Per ADR-017, the permitted-tables check is not a static list. It is built dynamically for each request from the physical tables (`Dataset.physical_table_name`) belonging to the requesting workspace, so a generated query can never reference another workspace's dataset even if it somehow referenced a physical table name directly.

Use parser-based validation rather than regex-only checks.

12. Read-Only Database Role

Queries must execute with a restricted role.

Even if SQL validation fails unexpectedly, the database role should prevent mutation.

Security should use multiple layers.

13. Query Result Limits

Server-side limits should protect against huge result sets.

For many analyses, aggregation should happen inside SQL.

Avoid:

SELECT millions of rows
→ send them to LLM

Prefer:

aggregate in SQL
→ return bounded result
14. Result Representation

Normalize SQL results into structured application objects.

Example:

{
  "columns": ["period", "refund_rate"],
  "rows": [
    ["before", 0.041],
    ["after", 0.052]
  ],
  "row_count": 2
}
15. Numerical Interpretation

The LLM may say:

Refund rate increased from 4.1% to 5.2%, a relative increase of approximately 26.8%.

But all numerical values must derive from query/calculation outputs.

Do not allow the model to perform important arithmetic only in prose.

16. Metric Tools

Common business calculations may become deterministic tools.

Potential examples:

calculate_refund_rate
calculate_average_delivery_time
calculate_percentage_change
calculate_revenue_impact

Do not create dozens of narrow tools prematurely.

Create one when:

logic is reused,
correctness matters,
SQL-only implementation becomes unclear.

These functions are internal to the analytics layer, not separately agent-facing tools. The agent calls the single `calculate_metric` tool (AGENT_SYSTEM.md §13), which dispatches to whichever of these internal functions matches the requested metric type.
17. Percentage Change

Be explicit about:

absolute change,
relative percentage change,
percentage-point change.

Example:

4% → 5%

Absolute percentage-point increase:

1 percentage point

Relative increase:

25%

Never mix these silently.

18. Time Windows

Business questions frequently involve ambiguous periods:

this month

before migration

recently

The analysis layer should resolve time windows explicitly using:

dataset range,
known event dates,
current/demo date context.

The resolved period should be included in analysis traces.

19. Missing Data

If required fields are missing:

Do not fabricate an analysis.

Return a clear insufficiency state.

Example:

Revenue impact cannot be estimated because refund_amount is unavailable.

20. Data Quality

V1 assumes reasonably clean Northstar data.

Still detect obvious issues such as:

null required columns,
invalid types,
impossible dates.

Do not build a complete automated data-cleaning platform.

21. Statistical Analysis

V1 may support basic:

descriptive statistics,
comparisons,
trends,
correlations,
anomaly detection.

Advanced inference should only be added when methodologically justified.

Do not use words such as "caused" solely because two metrics correlate.

22. Correlation vs Causation

OpsPilot may generate causal hypotheses.

The final language must reflect evidence strength.

Preferred:

The evidence strongly suggests the shipping migration was a major driver.

Avoid:

The migration definitively caused all refunds.

unless the data actually supports such certainty.

23. Anomaly Detection

Initial anomaly detection should favor simple interpretable approaches.

Examples:

rolling baseline deviation,
z-score where appropriate,
percentage-change thresholds.

Do not add complex ML solely for appearance.

24. Revenue Impact

Revenue-impact estimates must expose methodology.

Example:

Direct refunded revenue = $X

Estimated repeat-purchase risk = $Y

Total estimated impact = $X + estimated component Y

Clearly distinguish exact observed values from estimates.

25. Chart Generation

The analytics engine should produce chart specifications/data.

Example:

{
  "type": "line",
  "title": "Refund Rate by Day",
  "x": ["Jul 1", "Jul 2"],
  "series": [
    {
      "name": "Refund Rate",
      "values": [0.031, 0.034]
    }
  ]
}

The frontend renders the chart.

Do not use image generation for normal analytical charts.

26. Evidence Integration

Every important analytical result should be convertible into Evidence.

Evidence should include enough information to reproduce the result:

SQL or normalized calculation,
dataset IDs,
bounded result,
metric definition.
27. Analytics Observability

Track:

selected datasets,
schema context,
analysis plan,
generated SQL,
validation outcome,
execution time,
returned row count,
failures.

This makes incorrect analyses debuggable.

28. Retry Behavior

Do not retry invalid SQL unchanged.

Possible flow:

Generated SQL
↓
Validation failure
↓
Return structured validation feedback
↓
Allow one/few bounded correction attempts

All retries must be traceable.

29. Failure Modes

Potential failures:

no relevant dataset,
ambiguous schema,
validation failure,
SQL execution error,
timeout,
empty result,
insufficient data.

Each should produce a structured error rather than generic text.

30. Evaluation

Analytics evaluation uses the questions tagged `analytics` in the canonical evaluation question bank (DATASET.md §33) — it does not maintain its own separate question set. Each `analytics`-tagged question should have a deterministic expected result attached (e.g. refund rate before July 11, average delivery time by provider, shipping ticket change after July 11).

Compare computed outputs to known ground truth.

31. V1 Definition of Done

The Analytics Engine is ready when:

datasets are discoverable through a catalog,
relationships are represented,
analysis planning works,
safe SQL can be generated,
SQL validation blocks unsafe queries,
read-only execution works,
results are normalized,
important calculations are deterministic,
charts can be produced from results,
known Northstar questions match ground truth.
32. Core Rule

The LLM decides:

What should we calculate?

The database/tools determine:

What is the actual value?

The LLM then explains:

What does that value mean?