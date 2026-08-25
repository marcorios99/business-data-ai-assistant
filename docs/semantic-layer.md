# Semantic Layer

A semantic layer makes business meaning explicit above physical tables and columns. It can define verified metrics, relationships, dimensions, filters, naming, and business concepts so that a text-to-SQL model receives meaningful, constrained context instead of only raw schema metadata.

For a small local LLM, this semantic grounding may reduce ambiguity around identifiers, joins, and business definitions. Its value remains a hypothesis to test through the benchmark; no accuracy result is claimed yet.

## Candidate implementation

Wren with MDL will be evaluated as a candidate open-source semantic-layer infrastructure through a proof of concept. It is not yet installed, integrated, or validated in this project. The POC will start with a small Sales model using only a few WideWorldImporters tables and manually validated semantic queries.

If the POC succeeds, Inventory and Procurement can follow. If it is impractical or overly complex, the project may retain the experimental methodology with another semantic representation.

## Requirements for semantic grounding

Any representation used in the experiments should make metrics, relationships, and business concepts explicit, reviewable, and verifiable against WideWorldImporters. A concrete catalog of metrics will be documented only after validation on that database.
