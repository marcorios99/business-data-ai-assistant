"""Historical promotions and eligible product assignments."""

import random
import sqlite3

from scripts.dataset.config import DatasetConfig

CAMPAIGNS = (
    ("SUMMER", "Summer Tech", "PERCENTAGE", 10.0, None, "2024-01-10", "2024-01-31"),
    ("SCHOOL", "Back to School", "PERCENTAGE", 15.0, None, "2024-02-15", "2024-03-15"),
    ("MIDYEAR", "Mid-Year Deals", "FIXED_AMOUNT", None, 2_000, "2025-07-10", "2025-07-25"),
    ("CYBER", "Cyber Week", "PERCENTAGE", 20.0, None, "2025-11-20", "2025-11-30"),
    ("CHRISTMAS", "Christmas Campaign", "PERCENTAGE", 12.0, None, "2025-12-10", "2025-12-24"),
)


def generate_promotions(connection: sqlite3.Connection, config: DatasetConfig, random_source: random.Random) -> int:
    products = [row[0] for row in connection.execute("SELECT product_id FROM products")]
    rows, mappings = [], []
    for identifier, campaign in enumerate(CAMPAIGNS, 1):
        code, name, kind, percent, amount, start, end = campaign
        rows.append((identifier, f"PR-{code}-{identifier:02d}", name, kind, percent, amount, start, end, "COMPLETED"))
        for product_id in random_source.sample(products, min(len(products), 35 + identifier * 10)):
            mappings.append((identifier, product_id))
    connection.executemany("INSERT INTO promotions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.executemany("INSERT INTO promotion_products VALUES (?, ?)", mappings)
    return len(rows)
