# OpsPilot — Northstar Commerce Demo Dataset

## 1. Purpose

Northstar Commerce is the controlled synthetic business environment used to:

* develop OpsPilot,
* test analytics,
* test RAG,
* test agent investigations,
* evaluate evidence quality,
* demonstrate the final product.

The dataset must behave like a coherent business system.

It must not be a collection of unrelated random rows.

Important relationships and business events should be intentionally embedded while still containing realistic noise.

---

# 2. Demo Company

## Company

Northstar Commerce

## Business

Mid-sized online retail company selling consumer electronics and accessories.

## Primary Sales Channel

Direct-to-consumer e-commerce.

## Customer Support

Customers can contact support for:

* delivery issues,
* refunds,
* defective products,
* account problems,
* billing questions,
* product questions.

---

# 3. Dataset Time Period

Initial dataset period:

```text
June 1 → July 31
```

The primary investigation focuses on July.

This provides:

* baseline period,
* incident period,
* post-incident behavior.

Exact year should be consistent across all generated data.

---

# 4. Primary Hidden Business Event

## July 11 — Shipping Provider Migration

Northstar Commerce transitions a substantial share of deliveries from:

```text
SwiftShip
```

to:

```text
RapidShip Logistics
```

The migration is intended to reduce shipping costs.

However, RapidShip experiences operational issues during the first weeks.

---

# 5. Intended Effects

The synthetic data should produce approximately the following patterns.

These values are targets, not hardcoded outputs.

## Average Delivery Time

Before migration:

```text
~2.8 days
```

After migration:

```text
~4.5–4.8 days
```

---

## Shipping-Related Support Tickets

Increase approximately:

```text
40–50%
```

---

## Refund Requests

Increase approximately:

```text
20–30%
```

---

## Customer Rating

Approximate movement:

```text
4.3 → 3.8
```

among affected deliveries.

---

## Repeat Purchase Behavior

Customers affected by severe delivery delays should have lower probability of purchasing again during the observed period.

Target decrease:

```text
~10%
```

compared with similar unaffected customers.

---

# 6. Important Principle

The relationship must not be perfect.

Realistic data should include:

* unaffected RapidShip orders,
* delayed SwiftShip orders,
* refunds unrelated to shipping,
* customers who complain but do not refund,
* customers who refund without contacting support,
* unrelated product defects,
* normal random variation.

OpsPilot should identify a strong pattern rather than a perfectly deterministic rule.

---

# 7. Structured Datasets

Initial CSV datasets:

```text
customers.csv
products.csv
orders.csv
refunds.csv
support_tickets.csv
```

Optional later dataset:

```text
reviews.csv
```

Avoid unnecessary dataset proliferation in the first implementation.

---

# 8. customers.csv

## Purpose

Customer identity and segmentation.

## Columns

```text
customer_id
created_at
country
city
customer_segment
acquisition_channel
lifetime_orders
lifetime_value
```

## customer_segment

Example values:

```text
new
regular
high_value
```

## acquisition_channel

Example values:

```text
organic
paid_search
social
referral
email
```

## Target Size

Approximately:

```text
3,000 customers
```

---

# 9. products.csv

## Purpose

Product metadata.

## Columns

```text
product_id
product_name
category
brand
unit_price
unit_cost
active
```

## Categories

Examples:

```text
headphones
keyboards
mice
chargers
smart_home
accessories
```

## Target Size

Approximately:

```text
80–120 products
```

---

# 10. orders.csv

## Purpose

Primary commerce and delivery dataset.

## Columns

```text
order_id
customer_id
product_id

order_date
shipped_at
delivered_at

shipping_provider

quantity
unit_price
total_amount

order_status

delivery_days

is_delayed
```

## shipping_provider

```text
SwiftShip
RapidShip
```

## order_status

Examples:

```text
delivered
refunded
cancelled
in_transit
```

## is_delayed

Derived using a documented operational threshold.

Example:

```text
delivery_days > 4
```

This threshold should be documented and not silently changed.

## Target Size

Approximately:

```text
15,000 orders
```

---

# 11. Shipping Provider Distribution

Before July 11:

RapidShip should account for little or no normal traffic.

After July 11:

A substantial share of orders should use RapidShip.

Example target:

```text
60–75% RapidShip
25–40% SwiftShip
```

This creates an opportunity for comparative analysis.

---

# 12. Delivery Delay Generation

SwiftShip baseline:

```text
mean ~2.8 days
```

RapidShip during incident:

```text
mean ~4.6 days
```

Use distributions rather than fixed values.

Include:

* early deliveries,
* normal deliveries,
* moderate delays,
* severe delays.

Severe RapidShip delays should occur at a meaningfully higher rate.

---

# 13. refunds.csv

## Purpose

Track refund events.

## Columns

```text
refund_id
order_id
customer_id

refund_requested_at
refund_completed_at

refund_reason
refund_amount

status
```

## refund_reason

Examples:

```text
late_delivery
damaged_product
wrong_item
product_quality
changed_mind
billing_issue
other
```

## Target Size

Approximately:

```text
700–900 refunds
```

---

# 14. Refund Probability

Baseline refund probability should remain relatively low.

After severe shipping delays:

Probability of:

```text
late_delivery
```

refunds should increase significantly.

Not every delayed order should refund.

Not every refund after July 11 should be caused by RapidShip.

---

# 15. support_tickets.csv

## Purpose

Provide customer-language evidence.

## Columns

```text
ticket_id
customer_id
order_id

created_at
category
priority
channel

subject
message

status
resolution_time_hours
sentiment
```

## category

Examples:

```text
shipping
refund
product_issue
billing
account
general
```

## channel

Examples:

```text
email
chat
web
```

## Target Size

Approximately:

```text
2,000 tickets
```

---

# 16. Support Ticket Content

Ticket text should be synthetic but realistic.

Shipping-related examples may mention concepts such as:

* package has not arrived,
* expected delivery date passed,
* tracking has not updated,
* delivery is taking too long,
* request for cancellation,
* refund because of delay.

Do not repeat identical templates excessively.

Use controlled variation.

---

# 17. Ticket Sentiment

Possible values:

```text
positive
neutral
negative
```

Delayed orders should have increased probability of negative sentiment.

Sentiment does not need to be perfectly aligned with ticket category.

---

# 18. Optional reviews.csv

This dataset should be added only if the product needs an additional customer-feedback source.

Potential fields:

```text
review_id
customer_id
order_id
created_at
rating
review_text
```

Delayed RapidShip orders should show a measurable rating reduction.

This is optional for the initial implementation.

---

# 19. Business Documents

Initial documents:

```text
Refund Policy.pdf
Shipping Policy.pdf
Customer Support Handbook.pdf
Shipping Provider Migration Report.pdf
July Operations Incident Report.pdf
```

These should contain information useful for different investigation types.

---

# 20. Refund Policy

Should describe:

* refund eligibility,
* refund windows,
* delivery-delay handling,
* refund approval rules.

The policy should not contain the hidden causal conclusion.

It provides business context only.

---

# 21. Shipping Policy

Should describe:

* normal delivery targets,
* expected delivery windows,
* delayed-order procedures,
* shipping-provider responsibilities.

Example target:

Standard delivery:

```text
2–4 business days
```

This makes delayed orders analytically meaningful.

---

# 22. Customer Support Handbook

Should describe:

* escalation rules,
* delayed-shipment procedure,
* refund escalation,
* high-value customer handling.

Useful for recommendation generation.

---

# 23. Shipping Provider Migration Report

Contains the factual business event.

Should indicate:

* provider migration date,
* previous provider,
* new provider,
* business motivation,
* expected benefit.

Example:

```text
Migration date: July 11
Reason: reduce fulfillment cost
Expected shipping cost reduction: ~12%
```

Do not explicitly state that the migration caused refund increases.

OpsPilot should infer the relationship from multiple sources.

---

# 24. July Operations Incident Report

Contains operational observations.

Possible information:

* RapidShip tracking delays,
* warehouse handoff problems,
* increased customer escalations,
* internal monitoring notes.

This document may provide supporting evidence but should not directly answer the main demo question.

---

# 25. Primary Investigation

## Question

> Why did refunds increase this month?

## Expected Investigation Path

A strong investigation should approximately:

1. establish whether refunds actually increased,
2. identify when the increase began,
3. segment refunds by reason,
4. notice late-delivery refunds increased,
5. inspect delivery times,
6. identify RapidShip as disproportionately affected,
7. inspect support tickets,
8. detect increased shipping complaints,
9. search internal documents,
10. discover the July 11 provider migration,
11. estimate business impact,
12. produce recommendations.

This is not a hardcoded tool sequence.

The agent may use a different valid path.

---

# 26. Expected Primary Conclusion

A defensible conclusion should be similar to:

Refunds increased primarily due to delivery delays following the July 11 transition to RapidShip Logistics.

The conclusion should be supported by several independent signals.

Potential evidence:

* refund trend,
* refund-reason distribution,
* delivery-time increase,
* provider comparison,
* shipping-ticket increase,
* migration documentation.

---

# 27. Secondary Investigations

## Investigation A

> Which customer segment was most affected?

Expected analysis:

* segment customers,
* measure delayed orders,
* refunds,
* support tickets,
* potential revenue impact.

---

## Investigation B

> What changed around July 11?

Expected sources:

* timeline analytics,
* internal migration document,
* delivery metrics.

---

## Investigation C

> How much revenue is at risk?

Possible methodology:

* refunded revenue,
* affected order value,
* repeat-purchase decline,
* high-value customers affected.

The methodology must be explicit.

Avoid pretending an estimate is exact.

---

## Investigation D

> Which products have the highest refund rate?

This should be a primarily structured-data investigation.

---

## Investigation E

> What should Northstar do next?

Recommendations should draw from:

* analytical evidence,
* policies,
* incident context,
* customer feedback.

---

# 28. Ground Truth File

Dataset generation should produce a private development artifact describing known synthetic truths.

Example:

```text
ground_truth.json
```

Potential content:

```json
{
  "primary_incident": {
    "date": "YYYY-07-11",
    "event": "shipping_provider_migration",
    "provider": "RapidShip"
  },
  "expected_patterns": {
    "delivery_time": "increase",
    "shipping_tickets": "increase",
    "refunds": "increase"
  }
}
```

This file is for:

* evaluation,
* testing,
* debugging.

The runtime agent must never use this file as a knowledge source.

---

# 29. Dataset Generation

Dataset generation should be reproducible.

Use a fixed random seed.

Example concept:

```text
DATASET_SEED=...
```

Generation code should allow the same dataset to be recreated.

Important parameters should be configurable.

Examples:

* customer count,
* order count,
* incident date,
* baseline refund rate,
* RapidShip delay severity.

---

# 30. Validation Script

Create deterministic validation after generation.

The script should verify important properties.

Examples:

* RapidShip begins around the migration date,
* delivery time increases measurably,
* late-delivery refunds increase,
* support shipping complaints increase,
* datasets preserve valid foreign keys.

If these checks fail, the generated dataset should not be accepted.

---

# 31. Foreign Key Consistency

All generated relationships must remain valid.

Examples:

```text
orders.customer_id
→ customers.customer_id

orders.product_id
→ products.product_id

refunds.order_id
→ orders.order_id

support_tickets.order_id
→ orders.order_id
```

Do not generate orphan records unless deliberately testing malformed data.

---

# 32. Data Quality Noise

Later versions may intentionally include limited data-quality problems such as:

* missing values,
* inconsistent categories,
* duplicated records.

However, V1 should first prove the investigation engine with reasonably clean data.

Do not turn the initial project into a data-cleaning benchmark.

---

# 33. Canonical Evaluation Question Bank

This section is the single canonical source for OpsPilot's evaluation questions. RAG_SYSTEM.md, ANALYTICS_ENGINE.md, AGENT_SYSTEM.md, and TESTING.md each describe how their own layer *uses* this bank — none of them define a separate, independent question set. There is exactly one evaluation question file for the project (e.g. `evaluation_questions.json`, alongside `ground_truth.json`), not one per module.

Create an initial set containing approximately:

```text
15–25 questions
```

Every question carries one or more category tags from a fixed set: `retrieval`, `analytics`, `agent`, `e2e`. A single question may carry multiple tags (e.g. a multi-source investigation question is tagged both `agent` and `e2e`).

## retrieval

Example:

> What is the standard delivery window?

Consumed by RAG_SYSTEM.md's retrieval evaluation (Recall@K, Precision@K, MRR) and TESTING.md's retrieval evaluation dataset.

## analytics

Examples:

> What was the refund rate before July 11?

> Compare RapidShip and SwiftShip delivery times.

Consumed by ANALYTICS_ENGINE.md's evaluation (deterministic ground-truth comparison) and TESTING.md's analytics tests.

## agent / e2e

Examples:

> Why did refunds increase?

> What operational actions should Northstar prioritize?

Consumed by AGENT_SYSTEM.md's agent evaluation and TESTING.md's end-to-end acceptance tests. Questions requiring multi-source investigation or recommendation generation are tagged `agent`; the primary demo path additionally carries `e2e`.

## Format

Each entry should record at least: `id`, `question`, `tags`, and category-appropriate expected data (expected document for `retrieval`, expected computed value for `analytics`, expected evidence/behavior invariants for `agent`/`e2e` — see TESTING.md §14 on avoiding brittle exact-string tests for agent behavior).

---

# 34. Dataset Success Criteria

The dataset is ready when:

1. all files can be generated reproducibly,
2. relationships are valid,
3. the migration event is represented in documents,
4. the intended analytical signals exist,
5. signals contain realistic noise,
6. the primary conclusion can be independently verified,
7. at least five useful investigations are supported,
8. no application code needs hardcoded knowledge of the answer.

---

# 35. Core Rule

Northstar Commerce exists to test whether OpsPilot can discover business truth.

The dataset must never be designed so that OpsPilot appears correct without doing real retrieval and analysis.
