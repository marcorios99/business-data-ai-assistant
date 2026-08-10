"""SQL Server connection boundary for the WideWorldImporters reference database."""

from collections.abc import Mapping

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL

from app.core.config import Settings


def build_database_url(settings: Settings) -> URL:
    """Build a safe SQLAlchemy URL for local Windows Authentication."""
    return URL.create(
        "mssql+pyodbc",
        host=settings.db_server,
        database=settings.db_name,
        query={
            "driver": settings.db_driver,
            "Trusted_Connection": "yes" if settings.db_trusted_connection else "no",
            "Encrypt": "yes" if settings.db_encrypt else "no",
            "TrustServerCertificate": "yes" if settings.db_trust_server_certificate else "no",
        },
    )


def create_database_engine(settings: Settings) -> Engine:
    """Create a reusable SQL Server engine without embedding credentials."""
    return create_engine(build_database_url(settings), pool_pre_ping=True)


def check_database_connection(engine: Engine) -> Mapping[str, str]:
    """Return basic server metadata after a minimal connection check."""
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT @@SERVERNAME AS server_name, DB_NAME() AS database_name, SERVERPROPERTY('ProductVersion') AS version, SERVERPROPERTY('Edition') AS edition")
        ).mappings().one()
    return {key: str(value) for key, value in row.items()}
