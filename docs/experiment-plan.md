# Experiment Plan

## Research question

> How much does progressively structured database context improve the ability of a small local LLM to generate correct analytical SQL?

## Motivation

Small local language models are attractive for privacy, cost, and local development, but raw database schemas can be ambiguous and difficult to use reliably. This project evaluates whether semantic grounding improves text-to-SQL result correctness on WideWorldImporters running on Microsoft SQL Server.

The initial model is Qwen 3.5 4B run locally with Ollama. This is an evaluation project first and an application second.

## Experimental conditions

| Condition | Context supplied | Intended output flow |
| --- | --- | --- |
| A. Raw schema | Broad physical schema context | Qwen 3.5 4B generates SQL for SQL Server. |
| B. Scoped schema | Relevant schema subset | Qwen 3.5 4B generates SQL for SQL Server. |
| C. Semantic layer | Semantic context, potentially Wren MDL | The query flow will be defined by the Wren POC. |
| D. Semantic layer + examples | Semantic context plus verified NL-to-SQL examples or knowledge | Measures the additional value of verified examples. |

Wren is a candidate semantic-layer implementation to validate through a proof of concept, not an irreversible architectural commitment or completed integration.

## Benchmark design

The initial benchmark will contain approximately 40–60 manually verified business questions across Sales, Inventory, and Procurement. It will include different levels of difficulty; exact domain counts are intentionally not fixed yet.

Each item should have an independently prepared reference SQL query and/or reference result. The benchmark and reference answers must remain independent from the LLM under evaluation.

## Evaluation

Planned metrics are:

1. SQL validity
2. execution success
3. result correctness
4. identifier/schema errors
5. join errors
6. semantic interpretation errors
7. latency
8. prompt/context size

Result correctness has priority over execution success. A query can be syntactically valid and execute successfully while still giving a commercially incorrect answer.

### Error taxonomy

- **Identifier/schema errors:** invalid, missing, or incorrectly selected tables and columns.
- **Join errors:** wrong paths, cardinality assumptions, or duplicate/lost records caused by joins.
- **Semantic interpretation errors:** SQL that does not match the requested business meaning, measure, time scope, filter, or aggregation.
- **Validity and execution errors:** malformed or unsupported SQL, or SQL that fails at runtime.

## Roadmap

### Completed

**Hito 1 — Domain and dataset exploration**

- Synthetic SQLite prototype built.
- Prototype later replaced as the reference dataset.

**Hito 2A — SQL Server integration**

- WideWorldImporters restored locally.
- SQLAlchemy + pyodbc connection.
- Windows Authentication.
- Connection validated.

### Next

**Hito 3A — Wren proof of concept**

- Validate Wren installation and integration.
- Connect a minimal Sales model using only a few WideWorldImporters tables.
- Manually validate one or more semantic queries.

**Hito 3B — Minimal Sales semantic model**

- Define only concepts needed for the first experiments.

**Hito 4 — Raw-schema Qwen baseline**

**Hito 5 — Scoped-schema experiment**

**Hito 6 — Semantic-layer experiment**

**Hito 7 — Benchmark dataset**

- Manually verified business questions.
- Reference SQL and results.

**Hito 8 — Evaluation runner and error analysis**

**Hito 9 — Optional larger-model comparison**

**Hito 10 — FastAPI/frontend demo**

**Hito 11 — Portfolio polish and final report**

These milestones are a working roadmap, not a rigid architecture; they may change with experimental results.

## Scope constraints

1. The project is an evaluation project first and an application second.
2. Do not reimplement infrastructure already provided adequately by an open-source component unless doing so contributes directly to the experiment.
3. Prefer small vertical slices over large infrastructure milestones.
4. Each experimental condition must be independently reproducible.
5. The benchmark and reference answers must be independent of the LLM being evaluated.
6. SQL execution success alone is not considered correctness.
7. Wren is an experimental dependency, not an irreversible architectural commitment.
8. Avoid LangChain, LlamaIndex, vector databases, agent loops, RAG infrastructure, custom query planners, and large abstraction layers unless later evidence shows they are required.

## Optional model-size comparison

A later experiment may compare Qwen 3.5 4B with a larger local model, potentially Qwen 3.5 9B. It asks whether stronger semantic grounding can reduce the need for a substantially larger language model. This comparison is not an initial requirement and has no claimed outcome.

## Definition of success

The project succeeds if it produces a reproducible, manually grounded comparison that shows how each level of database context affects correct analytical answers, including failures and their causes. A functional demo is secondary to trustworthy benchmark design, reference SQL/results, and error analysis.
