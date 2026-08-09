"""Generate deterministic synthetic master data for the reference SQLite database."""

from __future__ import annotations

import argparse
import random
import sqlite3
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.create_database import DEFAULT_DATABASE_PATH, connect_database, create_database
from scripts.dataset.config import DatasetScale, get_dataset_config, validate_config_capacity
from scripts.dataset.generator import generate_master_data
from scripts.dataset.inventory import generate_initial_inventory, rebuild_inventory
from scripts.dataset.procurement import generate_purchase_orders
from scripts.dataset.validation import validate_master_data, validate_procurement_and_inventory


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
    validate_config_capacity(config)
    database_path = create_database(path, force=force)
    try:
        connection = connect_database(database_path)
        try:
            summary = generate_master_data(connection, config, seed)
            random_source = random.Random(seed + 1)
            initial_movements = generate_initial_inventory(connection, config, random_source)
            purchase_orders, purchase_items, purchase_movements = generate_purchase_orders(
                connection, config, random_source, initial_movements + 1
            )
            inventory_positions = rebuild_inventory(connection)
            summary.update({"purchase_orders": purchase_orders, "purchase_items": purchase_items, "initial_movements": initial_movements, "purchase_movements": purchase_movements, "inventory_positions": inventory_positions})
            validation_results = validate_master_data(connection, config) + validate_procurement_and_inventory(
                connection, config
            )
            connection.commit()
        except (OSError, RuntimeError, ValueError, sqlite3.Error):
            connection.rollback()
            raise
        finally:
            connection.close()
    except (OSError, RuntimeError, ValueError, sqlite3.Error):
        if database_path.exists():
            database_path.unlink()
        raise
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
        if name in {"purchase_orders", "purchase_items", "initial_movements", "purchase_movements", "inventory_positions"}:
            continue
        print(f"{name.replace('_', ' ').title():<20} {count:>6,}")
    print("\nProcurement")
    print(f"{'Purchase orders':<20} {summary['purchase_orders']:>6,}")
    print(f"{'Purchase items':<20} {summary['purchase_items']:>6,}")
    print("\nInventory")
    print(f"{'Initial movements':<20} {summary['initial_movements']:>6,}")
    print(f"{'Purchase movements':<20} {summary['purchase_movements']:>6,}")
    print(f"{'Inventory positions':<20} {summary['inventory_positions']:>6,}")
    print("\nValidation")
    for result in validation_results:
        print(f"OK {result}")


if __name__ == "__main__":
    main()
