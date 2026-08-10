# Base de datos de referencia

WideWorldImporters sobre Microsoft SQL Server es la base de referencia actual del
proyecto. El desarrollo local utiliza Windows Authentication mediante un SQL Server ODBC
Driver configurable; los valores de ejemplo se encuentran en `.env.example`.

Configure `DB_SERVER`, `DB_NAME`, `DB_DRIVER` y la política TLS apropiada para su entorno
en `.env`. `TrustServerCertificate=true` se contempla únicamente para desarrollo local.
Ejecute `python scripts/check_database.py` para comprobar conectividad y mostrar la
información básica del servidor y sus schemas.

El generador SQLite y sus 22 tablas permanecen temporalmente en el repositorio como un
artefacto histórico y prototipo sintético. No representan la base de referencia actual.
El modelo detallado de WideWorldImporters se documentará después de la introspección.
