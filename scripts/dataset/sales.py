"""Chronological sales simulation backed by the inventory movement ledger."""

from __future__ import annotations

import random
import sqlite3
from collections import defaultdict
from datetime import date, timedelta

from scripts.dataset.config import DatasetConfig


def _sale_dates(config: DatasetConfig, count: int, rng: random.Random) -> list[date]:
    dates = []
    span = (config.dataset_end_date - config.dataset_start_date).days
    for _ in range(count):
        candidate = config.dataset_start_date + timedelta(days=rng.randint(0, span))
        if candidate.month == 12 and rng.random() < 0.45:
            candidate = date(candidate.year, 12, rng.randint(1, 31))
        dates.append(candidate)
    return sorted(dates)


def generate_sales(connection: sqlite3.Connection, config: DatasetConfig, rng: random.Random) -> dict[str, int]:
    """Create completed sales only when chronologically available stock can fulfill them."""
    entries = connection.execute("SELECT warehouse_id, product_id, quantity_delta, occurred_at FROM inventory_movements WHERE movement_type IN ('INITIAL', 'PURCHASE') ORDER BY occurred_at, movement_id").fetchall()
    products = {row[0]: (row[1], row[2]) for row in connection.execute("SELECT product_id, base_price_cents, base_cost_cents FROM products")}
    sellers = defaultdict(list)
    for employee_id, store_id in connection.execute("SELECT employee_id, store_id FROM employees WHERE position != 'Store Manager'"):
        sellers[store_id].append(employee_id)
    stores = [row[0] for row in connection.execute("SELECT store_id FROM stores")]
    customers = connection.execute("SELECT customer_id, segment_id FROM customers").fetchall()
    promotions = connection.execute("SELECT promotion_id, promotion_type, discount_percent, discount_amount_cents, start_date, end_date FROM promotions").fetchall()
    eligible = {row for row in connection.execute("SELECT promotion_id, product_id FROM promotion_products")}
    stock, cursor, headers, items, payments, movements = defaultdict(int), 0, [], [], [], []
    movement_id = connection.execute("SELECT COALESCE(MAX(movement_id), 0) + 1 FROM inventory_movements").fetchone()[0]
    item_id, order_id = 1, 1
    for sale_date in _sale_dates(config, config.sales_orders, rng):
        while cursor < len(entries) and entries[cursor][3] <= sale_date.isoformat():
            warehouse_id, product_id, quantity, _ = entries[cursor]
            stock[warehouse_id, product_id] += quantity
            cursor += 1
        available = [(key, quantity) for key, quantity in stock.items() if quantity > 0]
        if not available:
            continue
        (warehouse_id, product_id), available_qty = rng.choice(available)
        customer_id, segment_id = rng.choice(customers)
        quantity = min(available_qty, 1 if segment_id == 1 else rng.randint(1, 3 if segment_id == 2 else 5))
        price, cost = products[product_id]
        price = max(cost, int(price * rng.uniform(0.97, 1.03)))
        active = [promotion for promotion in promotions if promotion[4] <= sale_date.isoformat() <= promotion[5] and (promotion[0], product_id) in eligible]
        promotion = rng.choice(active) if active and rng.random() < 0.75 else None
        gross = quantity * price
        discount = 0 if promotion is None else (gross * int(promotion[2]) // 100 if promotion[1] == "PERCENTAGE" else min(gross, promotion[3]))
        tax = ((gross - discount) * 18 + 50) // 100
        total = gross - discount + tax
        store_id = rng.choices(stores, weights=[4 if store == 1 else 1 for store in stores], k=1)[0]
        seller_id = rng.choice(sellers[store_id])
        channel = "B2B" if segment_id >= 3 else rng.choices(("STORE", "ONLINE", "B2B"), weights=(65, 30, 5), k=1)[0]
        headers.append((order_id, f"SO-{order_id:07d}", sale_date.isoformat(), store_id, customer_id, seller_id, channel, "COMPLETED", "PEN", gross, discount, tax, total))
        items.append((item_id, order_id, product_id, promotion[0] if promotion else None, quantity, price, cost, discount))
        payments.append((order_id, order_id, sale_date.isoformat(), "CARD" if segment_id == 1 else "BANK_TRANSFER", total, "SUCCESS", f"PAY-{order_id:07d}"))
        movements.append((movement_id, warehouse_id, product_id, "SALE", -quantity, "SALES_ORDER_ITEM", item_id, sale_date.isoformat(), None))
        stock[warehouse_id, product_id] -= quantity
        item_id += 1; movement_id += 1; order_id += 1
    connection.executemany("INSERT INTO sales_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", headers)
    connection.executemany("INSERT INTO sales_order_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)", items)
    connection.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)", payments)
    connection.executemany("INSERT INTO inventory_movements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", movements)
    return {"sales_orders": len(headers), "sales_items": len(items), "payments": len(payments), "sale_movements": len(movements), "promoted_items": sum(item[3] is not None for item in items)}
