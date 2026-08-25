# Architecture

## Current purpose

The architecture supports reproducible experiments in text-to-SQL rather than a production semantic-analytics engine. Each condition supplies a different level of database context to the same local LLM and is evaluated against WideWorldImporters on Microsoft SQL Server.

```text
                    WideWorldImporters
                           |
                    SQL Server metadata
                           |
              +------------+-------------+
              |            |             |
          raw schema    scoped schema   semantic layer
              |            |             |
              +------------+-------------+
                           |
                 local LLM: Qwen 3.5 4B
                           |
                    generated query
                           |
                       evaluator
                           |
                    Microsoft SQL Server
```

The semantic-layer branch may use Wren and MDL after a proof of concept. Wren is candidate infrastructure, not a completed integration. If it proves unsuitable, the experimental method can use another explicit and verifiable semantic representation.

## Experimental conditions

- **Raw schema:** broad physical schema context is provided to the local LLM.
- **Scoped schema:** only the relevant schema subset is provided.
- **Semantic layer:** semantic context or Wren MDL is provided; the final query flow depends on the Wren proof of concept.
- **Semantic layer + examples:** verified NL-to-SQL examples or other verified knowledge are added to semantic context.

All conditions should be independently reproducible and evaluated using the same benchmark and reference answers.

## Historical note

The initial design proposed a custom semantic registry, engine-neutral planner, SQL dialect layer, and deterministic SQL builder. Those components helped shape the early SQLite prototype, but they are not the required target architecture. The project now prioritizes testing existing semantic-layer infrastructure where appropriate over rebuilding it.
