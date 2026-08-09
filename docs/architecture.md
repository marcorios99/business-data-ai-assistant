# Architecture Notes

## Responsibilities

- `db/`: physical schema discovery and database-engine-specific behavior.
- `semantic/`: business meaning: domains, metrics, dimensions, filters, aliases, and relationships.
- `interpreter/`: local LLM communication and structured-intent interpretation.
- `planner/`: converts validated semantic intent into an engine-neutral query plan.
- `query/`: converts a query plan into parameterized SQL through a dialect.
- `repositories/`: executes generated queries and returns raw data.
- `services/`: application orchestration.
- `api/`: HTTP boundary only.

## Design constraint

The LLM should see only the semantic context relevant to the selected domain, not the full physical database schema.
