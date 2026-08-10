"""Application settings loaded from the local environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Local SQL Server connection settings using Windows Authentication."""

    db_server: str
    db_name: str
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_trusted_connection: bool = True
    db_encrypt: bool = False
    db_trust_server_certificate: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
