# Database Model

## Reference dataset

The current reference dataset is **WideWorldImporters** on **Microsoft SQL Server**. It is used to evaluate text-to-SQL without artificially adapting a database to the problem. Connection details and local setup are documented in [database.md](database.md).

## Legacy Synthetic Dataset

The synthetic SQLite dataset was the initial project prototype. It enabled validation of deterministic SQL generation and business relationships for a fictitious retail/distribution company.

It is no longer the reference dataset or the intended future model. WideWorldImporters replaced it so the experiments can work with an existing business database rather than one tailored to a custom architecture. Historical generator code remains temporarily in the repository. Its detailed 22-table description is retained in [dataset.md](dataset.md).
