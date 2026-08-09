"""Generate deterministic synthetic master data for the reference SQLite database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.create_database import DEFAULT_DATABASE_PATH, connect_database, create_database
from scripts.dataset.config import DatasetScale, get_dataset_config
from scripts.dataset.generator import generate_master_data
from scripts.dataset.validation import validate_master_data


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic business master data.")
    parser.add_argument("--scale", choices=[scale.value for scale in DatasetScale], default="demo")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--path", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--force", action="store_true", help="replace an existing database")
    return parser.parse_args()


def generate_dataset(path: Path, scale: DatasetScale | str, seed: int, *, force: bool = False) -> tuple[dict[str, int], list[str]]:
    """Create a database, populate master data, and validate it."""
    config = get_dataset_config(scale)
    database_path = create_database(path, force=force)
    with connect_database(database_path) as connection:
        summary = generate_master_data(connection, config, seed)
        validation_results = validate_master_data(connection, config)
    return summary, validation_results


def main() -> None:
    arguments = parse_arguments()
    try:
        summary, validation_results = generate_dataset(arguments.path, arguments.scale, arguments.seed, force=arguments.force)
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error
    print("Business dataset generated successfully\n")
    print(f"Path: {arguments.path.resolve()}\nScale: {arguments.scale}\nSeed: {arguments.seed}\n")
    print("Master data")
    for name, count in summary.items():
        print(f"{name.replace('_', ' ').title():<20} {count:>6,}")
    print("\nValidation")
    for result in validation_results:
        print(f"OK {result}")


if __name__ == "__main__":
    main()
