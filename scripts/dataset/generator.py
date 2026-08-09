"""Deterministic insertion of the dataset's master-data domain."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from scripts.dataset.config import DatasetConfig
from scripts.dataset.master_data import (
    BRAND_NAMES,
    CATEGORIES,
    CUSTOMER_SEGMENTS,
    FIRST_NAMES,
    LAST_NAMES,
    LOCATIONS,
    SUPPLIER_PREFIXES,
    SUPPLIER_SUFFIXES,
)
from scripts.dataset.patterns import SEGMENT_WEIGHTS, SUPPLIER_PROFILES, weighted_role


def random_date(random_source: random.Random, start: date, end: date) -> str:
    return (start + timedelta(days=random_source.randint(0, (end - start).days))).isoformat()


def generate_stores(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> None:
    rows = []
    for identifier in range(1, config.stores + 1):
        city, region, city_code = LOCATIONS[(identifier - 1) % len(LOCATIONS)]
        rows.append((identifier, f"ST-{city_code}-{identifier:03d}", f"{city} Retail Store", city, region,
                     random_date(random_source, date(2014, 1, 1), date(2026, 1, 1)), "ACTIVE"))
    connection.executemany("INSERT INTO stores VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


def generate_warehouses(connection: sqlite3.Connection, config: DatasetConfig) -> None:
    rows = []
    for identifier in range(1, config.warehouses + 1):
        city, region, city_code = LOCATIONS[(identifier - 1) % len(LOCATIONS)]
        store_id = None if identifier == 1 else ((identifier - 2) % config.stores) + 1
        name = "National Distribution Center" if identifier == 1 else f"{city} Regional Warehouse"
        rows.append((identifier, store_id, f"WH-{city_code}-{identifier:03d}", name, city, region, "ACTIVE"))
    connection.executemany("INSERT INTO warehouses VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


def generate_employees(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> None:
    rows = []
    for identifier in range(1, config.employees + 1):
        rows.append((identifier, f"EMP-{identifier:05d}", ((identifier - 1) % config.stores) + 1,
                     random_source.choice(FIRST_NAMES), random_source.choice(LAST_NAMES),
                     weighted_role(random_source),
                     random_date(random_source, date(2015, 1, 1), date(2026, 1, 1)), "ACTIVE"))
    connection.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)


def generate_categories(connection: sqlite3.Connection, config: DatasetConfig) -> None:
    rows = [(identifier, category[0], None) for identifier, category in enumerate(CATEGORIES[: config.categories], 1)]
    connection.executemany("INSERT INTO categories VALUES (?, ?, ?)", rows)


def generate_brands(connection: sqlite3.Connection, config: DatasetConfig) -> None:
    rows = [(identifier, name) for identifier, name in enumerate(BRAND_NAMES[: config.brands], 1)]
    connection.executemany("INSERT INTO brands VALUES (?, ?)", rows)


def generate_products(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> list[int]:
    rows = []
    base_costs = []
    for identifier in range(1, config.products + 1):
        category_id = ((identifier - 1) % config.categories) + 1
        _, items, price_range = CATEGORIES[category_id - 1]
        brand_id = ((identifier - 1) % config.brands) + 1
        brand = BRAND_NAMES[brand_id - 1]
        item = items[(identifier - 1) % len(items)]
        price = random_source.randint(*price_range)
        cost = int(price * random_source.uniform(0.55, 0.78))
        rows.append((identifier, f"SKU-{identifier:06d}", f"{brand} {item} Series {identifier:03d}", category_id,
                     brand_id, price, cost, "ACTIVE"))
        base_costs.append(cost)
    connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return base_costs


def generate_suppliers(connection: sqlite3.Connection, config: DatasetConfig) -> None:
    rows = []
    for identifier in range(1, config.suppliers + 1):
        city, region, _ = LOCATIONS[(identifier - 1) % len(LOCATIONS)]
        legal_name = f"{SUPPLIER_PREFIXES[(identifier - 1) % len(SUPPLIER_PREFIXES)]} {SUPPLIER_SUFFIXES[(identifier - 1) % len(SUPPLIER_SUFFIXES)]} {identifier:02d}"
        rows.append((identifier, f"SUP-{identifier:03d}", legal_name, city, region, "ACTIVE"))
    connection.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?)", rows)


def generate_supplier_products(
    connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random, base_costs: list[int]
) -> None:
    rows = []
    for product_id, base_cost in enumerate(base_costs, 1):
        supplier_count = random_source.randint(1, min(3, config.suppliers))
        supplier_ids = random_source.sample(range(1, config.suppliers + 1), supplier_count)
        for position, supplier_id in enumerate(supplier_ids):
            cost_factor, lead_time = SUPPLIER_PROFILES[position % len(SUPPLIER_PROFILES)]
            rows.append((supplier_id, product_id, f"SUPSKU-{supplier_id:03d}-{product_id:06d}",
                         max(1, int(base_cost * cost_factor)), lead_time, int(position == 0)))
    connection.executemany("INSERT INTO supplier_products VALUES (?, ?, ?, ?, ?, ?)", rows)


def generate_customer_segments(connection: sqlite3.Connection) -> None:
    connection.executemany("INSERT INTO customer_segments VALUES (?, ?, ?, ?)", CUSTOMER_SEGMENTS)


def generate_customers(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> None:
    rows = []
    for identifier in range(1, config.customers + 1):
        segment_id = random_source.choices((1, 2, 3, 4), weights=SEGMENT_WEIGHTS, k=1)[0]
        city, region, _ = random_source.choice(LOCATIONS)
        is_business = segment_id > 1
        tax_id = f"20{identifier:09d}" if is_business else None
        credit_limit = {1: 0, 2: 50_000, 3: 500_000, 4: 1_500_000}[segment_id]
        rows.append((identifier, f"CUS-{identifier:06d}", segment_id,
                     f"{random_source.choice(FIRST_NAMES)} {random_source.choice(LAST_NAMES)} {identifier:04d}",
                     tax_id, city, region,
                     random_date(random_source, date(2018, 1, 1), date(2026, 1, 1)), credit_limit, "ACTIVE"))
    connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)


def generate_master_data(connection: sqlite3.Connection, config: DatasetConfig, seed: int) -> dict[str, int]:
    """Populate only master tables as one atomic, reproducible transaction."""
    random_source = random.Random(seed)
    try:
        connection.execute("BEGIN")
        generate_stores(connection, config, random_source)
        generate_warehouses(connection, config)
        generate_employees(connection, config, random_source)
        generate_categories(connection, config)
        generate_brands(connection, config)
        base_costs = generate_products(connection, config, random_source)
        generate_suppliers(connection, config)
        generate_supplier_products(connection, config, random_source, base_costs)
        generate_customer_segments(connection)
        generate_customers(connection, config, random_source)
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    return {
        "stores": config.stores, "warehouses": config.warehouses, "employees": config.employees,
        "categories": config.categories, "brands": config.brands, "products": config.products,
        "suppliers": config.suppliers, "customers": config.customers,
    }
