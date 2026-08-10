"""Manually verify connectivity to the configured WideWorldImporters SQL Server database."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings
from app.db.connection import check_database_connection, create_database_engine


def main() -> None:
    try:
        settings = Settings()
        engine = create_database_engine(settings)
        metadata = check_database_connection(engine)
        with engine.connect() as connection:
            schemas = connection.execute(
                text("SELECT name FROM sys.schemas WHERE principal_id < 16384 AND name NOT IN ('sys', 'INFORMATION_SCHEMA') ORDER BY name")
            ).scalars().all()
    except (SQLAlchemyError, ValueError) as error:
        print("Database connection failed:")
        print(str(error).splitlines()[0])
        try:
            import pyodbc

            print(f"Available ODBC drivers: {', '.join(pyodbc.drivers()) or 'none'}")
        except ImportError:
            pass
        raise SystemExit(1) from error
    print("Database connection successful\n")
    print(f"Server: {metadata['server_name']}")
    print(f"Database: {metadata['database_name']}")
    print("Engine: Microsoft SQL Server")
    print(f"Version: {metadata['version']}")
    print(f"Edition: {metadata['edition']}\n")
    print("Schemas:")
    for schema in schemas:
        print(f"- {schema}")


if __name__ == "__main__":
    main()
