# Model Configuration for FactoryTwin Agents

This document outlines the recommended model assignments for each agent in the FactoryTwin system.

## Configuration

Two environment variables control all model selection:

- **`PRIMARY_MODEL`** — Used by all 70b agents (critical path)
- **`LIGHTWEIGHT_MODEL`** — Used by all 8b agents (supporting path)

### 70b Agents (Critical Path - High Reasoning)

| Agents | Env Variable | Default |
|--------|--------------|---------|
| intent_detector, endpoint_selector, query_decomposer, parameter_extractor, sql_generator, response_generator | `PRIMARY_MODEL` | llama-3.3-70b-versatile |

### 8b Agents (Supporting Path - Straightforward Tasks)

| Agents | Env Variable | Default |
|--------|--------------|---------|
| entity_extractor, plan_manager, general_chat_node | `LIGHTWEIGHT_MODEL` | llama-3.1-8b-instant |

## Environment Setup

Add these to your `.env` file:

```bash
# 70b Agents (Critical Path)
PRIMARY_MODEL=llama-3.3-70b-versatile

# 8b Agents (Supporting Path)
LIGHTWEIGHT_MODEL=llama-3.1-8b-instant
```

## Rationale

### Why 70b for Critical Path?

1. **intent_detector** — Must classify intent with context (conversation history, active plan, pending clarification). Errors cascade through entire pipeline.

2. **endpoint_selector** — Routes to 1 of 10 endpoints using complex domain-specific priority rules. Wrong endpoint = wrong data.

3. **query_decomposer** — Breaks multi-step queries into dependency graphs. Must distinguish sequential dependencies from parallel queries.

4. **parameter_extractor** — Each endpoint has unique parameters, date handling, and enum values. Requires endpoint-specific schema understanding.

5. **sql_generator** — Fuzzy matches user-provided names to 50+ DB candidates. Wrong match breaks the query.

6. **response_generator** — Converts data summaries to natural language while respecting domain context (months, currencies, part names). Must NOT invent data.

### Why 8b for Supporting Path?

1. **entity_extractor** — Receives already-structured GraphQL data and extracts top-10 entities. Deterministic task with fallback helpers.

2. **plan_manager** — Generates 1-2 sentence transitions between plan steps. Low complexity, low stakes.

3. **general_chat_node** — Fallback for out-of-scope queries and greetings. Not on critical path.

## Cost & Performance Impact

- **70b agents**: Higher latency (~2-3x), higher cost (~7x per token)
- **8b agents**: Lower latency (~1x), lower cost (~1x per token)

This split optimizes for accuracy on critical decisions while maintaining performance on supporting tasks.