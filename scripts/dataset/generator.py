"""Deterministic insertion of the dataset's master-data domain."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from scripts.dataset.config import DatasetConfig
from scripts.dataset.master_data import (
    BRAND_NAMES,
    BUSINESS_CORES,
    BUSINESS_PREFIXES,
    BUSINESS_SUFFIXES,
    CATEGORIES,
    CUSTOMER_SEGMENTS,
    FIRST_NAMES,
    LAST_NAMES,
    LOCATIONS,
    SUPPLIER_PREFIXES,
    SUPPLIER_SUFFIXES,
)
from scripts.dataset.patterns import (
    REGIONAL_WEIGHTS,
    SEGMENT_WEIGHTS,
    SUPPLIER_PROFILES,
    supplier_profile,
    weighted_role,
)


def random_date(random_source: random.Random, start: date, end: date) -> str:
    return (start + timedelta(days=random_source.randint(0, (end - start).days))).isoformat()


def generate_stores(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> None:
    rows = []
    for identifier in range(1, config.stores + 1):
        city, region, city_code = LOCATIONS[(identifier - 1) % len(LOCATIONS)]
        rows.append((identifier, f"ST-{city_code}-{identifier:03d}", f"{city} Retail Store", city, region,
                     random_date(random_source, date(2014, 1, 1), config.dataset_end_date), "ACTIVE"))
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
        store_id = ((identifier - 1) % config.stores) + 1
        role = "Store Manager" if identifier <= config.stores else weighted_role(random_source)
        rows.append((identifier, f"EMP-{identifier:05d}", store_id,
                     random_source.choice(FIRST_NAMES), random_source.choice(LAST_NAMES),
                     role, random_date(random_source, date(2015, 1, 1), config.dataset_end_date), "ACTIVE"))
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
    brand_ids = [identifier for identifier in range(1, config.brands + 1)]
    balanced_brands = (brand_ids * ((config.products + config.brands - 1) // config.brands))[: config.products]
    random_source.shuffle(balanced_brands)
    identifier = 1
    products_per_category, remainder = divmod(config.products, config.categories)
    for category_id in range(1, config.categories + 1):
        _, items, price_range = CATEGORIES[category_id - 1]
        category_count = products_per_category + int(category_id <= remainder)
        for product_offset in range(category_count):
            brand_id = balanced_brands[identifier - 1]
            brand = BRAND_NAMES[brand_id - 1]
            item = items[product_offset % len(items)]
            price = random_source.randint(*price_range)
            cost = int(price * random_source.uniform(0.55, 0.78))
            rows.append((identifier, f"SKU-{identifier:06d}", f"{brand} {item} Series {identifier:03d}", category_id,
                         brand_id, price, cost, "ACTIVE"))
            base_costs.append(cost)
            identifier += 1
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
        candidates = []
        for supplier_id in supplier_ids:
            cost_factor, lead_time_range = SUPPLIER_PROFILES[supplier_profile(supplier_id)]
            unit_cost = max(1, int(base_cost * cost_factor * random_source.uniform(0.97, 1.03)))
            lead_time = random_source.randint(*lead_time_range)
            candidates.append((supplier_id, unit_cost, lead_time))
        preferred_supplier_id = min(candidates, key=lambda row: (row[1] / base_cost) + (row[2] * 0.01))[0]
        for supplier_id, unit_cost, lead_time in candidates:
            rows.append((supplier_id, product_id, f"SUPSKU-{supplier_id:03d}-{product_id:06d}", unit_cost,
                         lead_time, int(supplier_id == preferred_supplier_id)))
    connection.executemany("INSERT INTO supplier_products VALUES (?, ?, ?, ?, ?, ?)", rows)


def generate_customer_segments(connection: sqlite3.Connection) -> None:
    connection.executemany("INSERT INTO customer_segments VALUES (?, ?, ?, ?)", CUSTOMER_SEGMENTS)


def generate_customers(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> None:
    rows = []
    for identifier in range(1, config.customers + 1):
        segment_id = random_source.choices((1, 2, 3, 4), weights=SEGMENT_WEIGHTS, k=1)[0]
        city, region, _ = random_source.choices(LOCATIONS, weights=REGIONAL_WEIGHTS, k=1)[0]
        is_business = segment_id > 1
        tax_id = f"20{identifier:09d}" if is_business else None
        credit_ranges = {1: (0, 10_000), 2: (20_000, 100_000), 3: (250_000, 900_000), 4: (800_000, 2_000_000)}
        credit_limit = random_source.randint(*credit_ranges[segment_id])
        name = (
            f"{random_source.choice(FIRST_NAMES)} {random_source.choice(LAST_NAMES)} {identifier:04d}"
            if not is_business
            else f"{random_source.choice(BUSINESS_PREFIXES)} {random_source.choice(BUSINESS_CORES)} {random_source.choice(BUSINESS_SUFFIXES)}"
        )
        rows.append((identifier, f"CUS-{identifier:06d}", segment_id,
                     f"{name} {identifier:04d}" if is_business else name, tax_id, city, region,
                     random_date(random_source, date(2018, 1, 1), config.dataset_end_date), credit_limit, "ACTIVE"))
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
    except sqlite3.Error:
        connection.rollback()
        raise
    return {
        "stores": config.stores, "warehouses": config.warehouses, "employees": config.employees,
        "categories": config.categories, "brands": config.brands, "products": config.products,
        "suppliers": config.suppliers, "customers": config.customers,
    }
