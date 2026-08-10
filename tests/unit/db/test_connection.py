"""Offline tests for SQL Server settings and URL construction."""

from app.core.config import Settings
from app.db.connection import build_database_url


def test_settings_accept_explicit_windows_authentication_values():
    settings = Settings(
        db_server="LOCALHOST\\SQLEXPRESS",
        db_name="WideWorldImporters",
        db_driver="ODBC Driver 18 for SQL Server",
        db_trusted_connection=True,
    )
    assert settings.db_server == "LOCALHOST\\SQLEXPRESS"
    assert settings.db_trusted_connection is True


def test_sql_server_url_uses_pyodbc_driver_and_windows_authentication():
    settings = Settings(db_server="LOCALHOST\\SQLEXPRESS", db_name="WideWorldImporters")
    url = build_database_url(settings)
    rendered = url.render_as_string(hide_password=True)
    assert url.drivername == "mssql+pyodbc"
    assert "driver=ODBC+Driver+18+for+SQL+Server" in rendered
    assert "Trusted_Connection=yes" in rendered
    assert url.username is None
    assert url.password is None
