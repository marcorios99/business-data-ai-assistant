# Business Data AI Assistant

An experimental text-to-SQL project investigating how much **structured semantic grounding** improves analytical SQL accuracy for small local language models.

The reference environment is **WideWorldImporters** on **Microsoft SQL Server**. The initial model is **Qwen 3.5 4B**, run locally with Ollama. **Wren** and its MDL semantic layer are candidates to be validated through a proof of concept; they are not integrated or validated yet.

## Experimental direction

The project will compare progressively richer context for the same business questions:

- raw physical schema;
- scoped schema relevant to the question;
- a semantic layer (potentially Wren/MDL);
- semantic layer plus verified examples or knowledge.

The goal is result correctness, not merely executable SQL. A small, manually verified benchmark of business questions will support the evaluation.

## Current status

Hito 2A is complete: WideWorldImporters has been restored locally and connectivity through SQLAlchemy + pyodbc with Windows Authentication has been validated. The next step is a minimal Wren proof of concept for Sales.

The previous synthetic SQLite generator remains temporarily in the repository as a historical prototype; it is no longer the reference dataset.

For the research question, methodology, roadmap, and scope, see the [experiment plan](docs/experiment-plan.md). See also the [architecture](docs/architecture.md) and [database setup](docs/database.md).
