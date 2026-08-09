"""Create the reference SQLite database from the ordered schema files."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIRECTORY = PROJECT_ROOT / "database" / "schema"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "business_demo.sqlite"


def connect_database(path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def schema_files() -> list[Path]:
    """Return schema scripts in dependency order."""
    return sorted(SCHEMA_DIRECTORY.glob("*.sql"))


def create_database(path: Path = DEFAULT_DATABASE_PATH, *, force: bool = False) -> Path:
    """Create an empty database, refusing to replace an existing one by default."""
    path = path.resolve()
    if path.exists():
        if not force:
            raise FileExistsError(f"Database already exists: {path}. Use --force to recreate it.")
        path.unlink()

    path.parent.mkdir(parents=True, exist_ok=True)
    scripts = schema_files()
    if not scripts:
        raise FileNotFoundError(f"No schema files found in {SCHEMA_DIRECTORY}")

    connection = connect_database(path)
    try:
        schema_sql = "\n".join(script.read_text(encoding="utf-8") for script in scripts)
        connection.executescript(f"BEGIN;\n{schema_sql}\nCOMMIT;")
    except sqlite3.Error as error:
        connection.rollback()
        raise RuntimeError(f"Failed to create database from schema: {error}") from error
    finally:
        connection.close()
    return path


def table_count(path: Path) -> int:
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the reference SQLite database.")
    parser.add_argument("--path", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--force", action="store_true", help="replace an existing database")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    try:
        database_path = create_database(arguments.path, force=arguments.force)
    except (FileExistsError, FileNotFoundError, RuntimeError) as error:
        raise SystemExit(f"Error: {error}") from error

    print("Database created successfully")
    print(f"Path: {database_path}")
    print(f"Tables: {table_count(database_path)}")
    print("Foreign keys: enabled")


if __name__ == "__main__":
    main()
