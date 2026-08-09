# Business Data AI Assistant

Clean project skeleton for a local semantic analytics engine.

## Core idea

The local LLM interprets a business question into a constrained semantic intent. It does not receive the whole database schema and it does not generate arbitrary SQL. The application selects the relevant semantic domain, validates the intent, plans the query, and generates SQL deterministically.

SQLite is the reference implementation so the demo can be reproduced without installing a database server. The architecture keeps database inspection and SQL dialect concerns isolated so PostgreSQL, SQL Server, or other relational engines can be added later through dedicated adapters.

## Planned flow

```text
User question
    -> domain routing
    -> local LLM interpretation
    -> structured semantic intent
    -> semantic validation
    -> query planner
    -> SQL dialect
    -> repository
    -> SQLite
```

## Project status

This ZIP intentionally contains architecture only. Business logic, SQL schema, dataset generation, semantic definitions, and UI will be implemented incrementally.
