"""Deterministic historical procurement generation and receipt ledger entries."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from scripts.dataset.config import DatasetConfig


def _random_date(random_source: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=random_source.randint(0, (end - start).days))


def _order_quantity(price_cents: int, random_source: random.Random) -> int:
    return max(2, (100_000 // max(price_cents, 1)) * random_source.randint(2, 6))


def generate_purchase_orders(
    connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random, movement_start_id: int
) -> tuple[int, int, int]:
    """Generate POs, received lines, and their matching PURCHASE ledger movements."""
    product_costs = dict(connection.execute("SELECT product_id, base_price_cents FROM products"))
    supplier_products: dict[int, list[tuple[int, int, int]]] = {}
    for supplier_id, product_id, unit_cost, lead_time in connection.execute(
        "SELECT supplier_id, product_id, unit_cost_cents, lead_time_days FROM supplier_products"
    ):
        supplier_products.setdefault(supplier_id, []).append((product_id, unit_cost, lead_time))
    supplier_ids = list(supplier_products)
    warehouse_ids = [row[0] for row in connection.execute("SELECT warehouse_id FROM warehouses")]
    headers, items, movements = [], [], []
    item_id, movement_id = 1, movement_start_id
    tax_rate_percent = 18
    for order_id in range(1, config.purchase_orders + 1):
        supplier_id = random_source.choice(supplier_ids)
        warehouse_id = random_source.choices(warehouse_ids, weights=[4] + [1] * (len(warehouse_ids) - 1), k=1)[0]
        order_date = _random_date(random_source, config.dataset_start_date, config.dataset_end_date)
        near_end = (config.dataset_end_date - order_date).days <= 21
        status = "RECEIVED"
        if near_end and random_source.random() < 0.30:
            status = random_source.choice(("OPEN", "PARTIALLY_RECEIVED"))
        available = supplier_products[supplier_id]
        item_count = min(len(available), random_source.randint(3, 15))
        selected = random_source.sample(available, item_count)
        max_lead = max(row[2] for row in selected)
        expected_date = min(config.dataset_end_date, order_date + timedelta(days=max_lead))
        received_date = None
        if status != "OPEN":
            received_date = min(config.dataset_end_date, max(order_date, expected_date + timedelta(days=random_source.randint(-2, 3))))
        subtotal = 0
        for product_id, contractual_cost, lead_time in selected:
            quantity_ordered = _order_quantity(product_costs[product_id], random_source)
            if status == "RECEIVED":
                quantity_received = quantity_ordered
            elif status == "PARTIALLY_RECEIVED":
                quantity_received = random_source.randint(1, quantity_ordered - 1)
            else:
                quantity_received = 0
            unit_cost = max(1, int(contractual_cost * random_source.uniform(0.98, 1.02)))
            items.append((item_id, order_id, product_id, quantity_ordered, quantity_received, unit_cost))
            subtotal += quantity_ordered * unit_cost
            if quantity_received:
                movements.append((movement_id, warehouse_id, product_id, "PURCHASE", quantity_received, "PURCHASE_ORDER_ITEM", item_id, received_date.isoformat(), None))
                movement_id += 1
            item_id += 1
        tax = (subtotal * tax_rate_percent + 50) // 100
        headers.append((order_id, f"PO-{order_id:06d}", supplier_id, warehouse_id, order_date.isoformat(), expected_date.isoformat(), received_date.isoformat() if received_date else None, status, "PEN", subtotal, tax, subtotal + tax))
    connection.executemany("INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", headers)
    connection.executemany("INSERT INTO purchase_order_items VALUES (?, ?, ?, ?, ?, ?)", items)
    connection.executemany("INSERT INTO inventory_movements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", movements)
    return len(headers), len(items), len(movements)
