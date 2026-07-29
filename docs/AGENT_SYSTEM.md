OpsPilot — Agent System Specification
1. Purpose

The Agent System is the orchestration layer that turns a business question into an evidence-backed investigation.

It connects:

RAG,
structured analytics,
deterministic calculations,
evidence collection,
recommendation generation.

The agent must be powerful enough to investigate flexibly but constrained enough to remain inspectable and testable.

2. Architecture

V1 uses:

One Orchestrator Agent
+
Explicit Tools

Do not introduce separate autonomous agents unless real evaluation shows a clear benefit.

3. Core Investigation Loop
User Question
↓
Understand Goal
↓
Create Investigation Plan
↓
Execute Next Step
↓
Call Tool
↓
Observe Result
↓
Store Evidence
↓
Update Hypotheses
↓
Need More Evidence?
├── Yes → Continue
└── No → Synthesize
↓
Recommendations
↓
Final Result
4. Agent Responsibilities

The orchestrator may:

interpret questions,
choose relevant investigation strategies,
create plans,
select tools,
inspect tool outputs,
decide whether evidence is sufficient,
form hypotheses,
identify contradictions,
synthesize findings,
recommend actions.
5. Agent Non-Responsibilities

The agent must not:

directly connect to databases,
directly access credentials,
execute arbitrary code,
modify infrastructure,
invent evidence,
execute unrestricted external actions,
ignore application permissions.

Capabilities exist only through approved tools.

6. Investigation State

Maintain explicit state.

Conceptually:

{
  "query": "...",
  "goal": "...",
  "plan": [],
  "current_step": null,
  "observations": [],
  "tool_executions": [],
  "evidence": [],
  "hypotheses": [],
  "findings": [],
  "recommendations": [],
  "status": "RUNNING"
}

Exact implementation may differ.

7. Investigation Plan

The initial plan should be structured.

Example:

{
  "steps": [
    {
      "title": "Measure refund trend",
      "goal": "Confirm whether refunds increased and identify timing."
    },
    {
      "title": "Analyze refund reasons",
      "goal": "Identify which refund categories drove the change."
    },
    {
      "title": "Investigate delivery performance",
      "goal": "Determine whether logistics changed during the same period."
    }
  ]
}

Plans may evolve when evidence changes.

8. Dynamic Planning

The agent should not rigidly execute every original step.

Example:

If the first analysis shows refunds did not increase:

the investigation should reconsider the user's premise.

The plan may:

add steps,
skip steps,
revise hypotheses.

Plan modifications should be traceable.

9. Tools

Initial tool set may include:

search_documents
query_database
calculate_metric
analyze_feedback
generate_chart

Tool count should remain intentionally small.

10. Tool Contract

Every tool must define:

name,
purpose,
input schema,
output schema,
permission requirements,
possible failures.

Tool descriptions should be specific enough for reliable selection.

11. search_documents

Purpose:

Retrieve relevant internal document evidence.

Input concept:

{
  "query": "...",
  "filters": {}
}

Output:

Evidence candidates with source metadata.

The tool must use the actual RAG system.

12. query_database

Purpose:

Perform safe structured analysis.

The tool should not simply accept arbitrary raw SQL from the agent.

Preferred architecture:

Agent analytical request
↓
Analytics Engine
↓
Plan / SQL generation
↓
Validation
↓
Execution
↓
Structured result

This keeps security inside the analytics module.

13. calculate_metric

Purpose:

Execute deterministic calculations when appropriate.

Examples:

percentage change,
rate,
ratio,
revenue-impact component.

Do not let the LLM invent computed numbers.

calculate_metric is the single agent-facing tool for deterministic calculations. It does not itself contain calculation logic; it dispatches by metric type to the internal deterministic functions defined in ANALYTICS_ENGINE.md §16 (e.g. `calculate_refund_rate`, `calculate_average_delivery_time`, `calculate_percentage_change`, `calculate_revenue_impact`). Those functions are internal to the analytics layer and are not separately registered as agent-facing tools — the agent only ever sees and calls `calculate_metric`.

14. analyze_feedback

Purpose:

Analyze customer-support text or related feedback.

Potential capabilities:

category distribution,
theme extraction,
sentiment aggregation,
representative evidence retrieval.

Avoid treating model-generated sentiment as exact ground truth.

15. generate_chart

Purpose:

Create structured chart specifications from verified analytical outputs.

It should not independently invent data.

16. Tool Selection

The model decides which approved tool to request.

The application validates:

tool exists,
input is valid,
user/workspace has permission,
execution limits are respected.
17. Tool Outputs

Tool results should be structured and concise.

Avoid returning enormous raw datasets into agent context.

Prefer:

summaries,
bounded rows,
metrics,
evidence IDs,
chart data.
18. Evidence Collection

Tool outputs that support conclusions should become Evidence records.

Evidence exists independently from final prose.

The agent references evidence IDs.

19. Hypotheses

The agent may maintain hypotheses such as:

H1: Shipping delays drove refund growth.
H2: Product quality problems drove refund growth.

Hypotheses are not facts.

They must be tested against evidence.

20. Hypothesis Updates

A hypothesis may be:

proposed,
supported,
weakened,
rejected.

Do not require formal Bayesian inference for V1.

The important goal is explicit reasoning state and evidence comparison.

21. Contradictory Evidence

If evidence conflicts:

the agent should not silently choose whichever result supports the current story.

It should:

inspect the conflict,
potentially gather more evidence,
record a structured contradiction signal,
explain the ambiguity in the synthesized findings.

A contradiction signal is structured state, not a self-assessed number. Conceptually:

{
  "contradiction_id": "...",
  "conflicting_evidence_ids": ["...", "..."],
  "description": "Refund-reason breakdown suggests billing issues, but support ticket volume shows no billing spike.",
  "resolved": false
}

The agent does not itself decide how much this should lower confidence. It only records that the contradiction exists. The application's deterministic confidence model (§29) consumes unresolved contradiction signals as one of its measurable inputs. This keeps "the agent noticed a conflict" (an observation) separate from "how much should this affect confidence" (a deterministic calculation), consistent with ADR-011.
22. Stopping Conditions

The agent should stop when:

investigation goals have been sufficiently addressed,
important findings have supporting evidence,
additional tools are unlikely to materially change the answer,
execution limits are reached,
required data is unavailable.
23. Execution Limits

Configure maximum values such as:

max_steps
max_tool_calls
max_llm_calls
max_execution_time

The exact values should be tuned experimentally.

The agent must never run an unbounded loop.

24. Insufficient Evidence

If evidence is insufficient:

the agent should return that state honestly.

Example:

Refunds increased, but the available data is insufficient to determine the primary cause reliably.

This is preferable to fabricating a confident root cause.

25. Findings

Findings should be structured before final prose.

Concept:

{
  "statement": "Late-delivery refunds increased after July 11.",
  "importance": "high",
  "evidence_ids": ["..."],
  "confidence": {}
}
26. Recommendations

Recommendations should be connected to findings.

Example:

Finding:

RapidShip delivery delays correlate strongly with increased refunds.

Recommendation:

Review the RapidShip SLA and create proactive alerts for orders delayed beyond four days.

Recommendations should not appear without analytical justification.

27. Action Execution

V1 primarily recommends actions.

External operational execution is out of scope.

Future action architecture should separate:

Recommendation
↓
User Approval
↓
Authorized Action Tool
↓
Audited Execution

Do not conflate recommendations with automatic side effects.

28. Final Result

The agent should eventually output structured data similar to:

{
  "summary": "...",
  "findings": [],
  "recommendations": [],
  "evidence_ids": [],
  "charts": [],
  "confidence": {}
}

Frontend prose can be generated from this structure.

29. Confidence

Do not ask the LLM:

How confident are you from 0 to 100?

and present that value as meaningful.

The LLM must never directly assign the final confidence value, at the investigation level or the finding level. Confidence is always a structured object (matching Investigation.confidence in DATA_MODEL.md §12), computed deterministically by the application from measurable signals such as:

evidence coverage,
analytical support,
source agreement,
unresolved contradiction signals (§21),
retrieval quality.

The agent's role is limited to producing the raw inputs to this calculation — evidence, findings, and contradiction signals. It does not compute or state the resulting confidence value itself.
30. Agent Prompt Design

System prompts should clearly establish:

product role,
tool boundaries,
evidence requirements,
safety rules,
stopping behavior,
handling of insufficient data.

Prompts should remain versioned and testable.

31. Retrieved Content

Retrieved document content must be clearly labeled as untrusted evidence.

Documents cannot:

modify agent permissions,
alter system rules,
request secrets,
instruct tools outside the user's request.
32. Agent Memory

V1 should use investigation-scoped state.

Do not introduce long-term autonomous memory without a clear product requirement.

Historical investigations remain stored as application data but are not automatically treated as agent memory.

33. Context Management

Do not continuously append every tool result forever.

Context should contain:

current goal,
plan,
important observations,
relevant evidence summaries.

Large raw outputs should remain outside model context and be referenced structurally.

34. Parallel Tool Calls

Independent analytical tasks may eventually execute in parallel.

Example:

analyze refund trend
+
search migration documents

Parallel execution should only be introduced when:

tool dependencies are clear,
tracing remains understandable,
it meaningfully reduces latency.

Correctness comes first.

35. Retry Policy

Agent-level retries should be bounded.

Examples:

Structured output parse failure:

retry with validation feedback

Tool failure:

retry only when failure is transient and tool is safe

Do not retry blindly.

36. Error Handling

The agent should distinguish:

tool unavailable,
no data,
validation error,
timeout,
provider failure,
insufficient evidence.

Errors should remain visible in investigation traces.

37. Observability

Persist or expose:

plan creation,
plan changes,
step status,
tool calls,
tool durations,
tool errors,
LLM calls,
evidence creation,
final synthesis.

The goal is to answer:

Why did the agent produce this result?

38. Agent Evaluation

Do not evaluate only final prose.

Measure behavior.

Possible checks:

appropriate tools used,
unnecessary tools avoided,
correct evidence discovered,
numerical facts match analytics,
unsupported claims avoided,
investigation terminates.
39. Primary Evaluation

Agent evaluation uses the questions tagged `agent`/`e2e` in the canonical evaluation question bank (DATASET.md §33) — it does not maintain its own separate question set. The primary such question:

Why did refunds increase this month?

Expected broad behavior:

verify refund trend,
identify change timing,
inspect refund reasons,
investigate shipping/delivery data,
discover RapidShip migration evidence,
connect several independent signals,
provide supported recommendations.

The exact sequence does not need to be identical.

40. V1 Definition of Done

The agent system is ready when:

structured investigation plans work,
approved tools can be called,
tool results update explicit state,
evidence is stored during investigation,
plans can adapt,
execution is bounded,
insufficient evidence is handled honestly,
final findings reference evidence,
recommendations derive from findings,
primary Northstar investigation succeeds reliably.
41. Core Rule

The agent is an orchestrator.

It should decide:

What evidence do I need next?

It should not decide:

What facts would make the best story?