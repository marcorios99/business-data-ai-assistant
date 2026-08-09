"""Initial inventory ledger generation and inventory projection rebuilds."""

from __future__ import annotations

import random
import sqlite3

from scripts.dataset.config import DatasetConfig
from scripts.dataset.patterns import stock_quantity


def generate_initial_inventory(
    connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random
) -> int:
    """Create positive INITIAL movements before materializing inventory positions."""
    products = connection.execute("SELECT product_id, base_price_cents FROM products").fetchall()
    warehouse_ids = [row[0] for row in connection.execute("SELECT warehouse_id FROM warehouses")]
    rows = []
    movement_id = 1
    for product_id, price_cents in products:
        rows.append((movement_id, 1, product_id, "INITIAL", stock_quantity(price_cents, central=True, random_source=random_source), None, None, config.dataset_start_date.isoformat(), None))
        movement_id += 1
        for warehouse_id in warehouse_ids[1:]:
            if random_source.random() < 0.65:
                rows.append((movement_id, warehouse_id, product_id, "INITIAL", stock_quantity(price_cents, central=False, random_source=random_source), None, None, config.dataset_start_date.isoformat(), None))
                movement_id += 1
    connection.executemany("INSERT INTO inventory_movements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return len(rows)


def rebuild_inventory(connection: sqlite3.Connection) -> int:
    """Materialize current inventory only from its movement ledger."""
    connection.execute("DELETE FROM inventory")
    connection.execute(
        """
        INSERT INTO inventory (warehouse_id, product_id, quantity_on_hand, quantity_reserved, reorder_point, updated_at)
        SELECT warehouse_id, product_id, SUM(quantity_delta), 0,
               MAX(1, SUM(quantity_delta) / 4), MAX(occurred_at)
        FROM inventory_movements
        GROUP BY warehouse_id, product_id
        """
    )
    return connection.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
