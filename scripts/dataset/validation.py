"""Readable integrity checks for the generated master data."""

import sqlite3

from scripts.dataset.config import DatasetConfig


class DatasetValidationError(ValueError):
    """Raised when a generated dataset violates a required invariant."""


def _scalar(connection: sqlite3.Connection, query: str) -> int:
    return connection.execute(query).fetchone()[0]


def validate_master_data(connection: sqlite3.Connection, config: DatasetConfig) -> list[str]:
    """Validate master data and return names of the checks that passed."""
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise DatasetValidationError("Foreign key check failed.")
    expected_counts = {
        "stores": config.stores, "warehouses": config.warehouses, "employees": config.employees,
        "categories": config.categories, "brands": config.brands, "products": config.products,
        "suppliers": config.suppliers, "customers": config.customers,
    }
    for table, expected in expected_counts.items():
        if _scalar(connection, f"SELECT COUNT(*) FROM {table}") != expected:
            raise DatasetValidationError(f"Unexpected row count for {table}.")
    if _scalar(connection, "SELECT COUNT(*) FROM products WHERE base_cost_cents >= base_price_cents"):
        raise DatasetValidationError("Product cost must be lower than product price.")
    if _scalar(connection, "SELECT COUNT(*) FROM supplier_products WHERE unit_cost_cents <= 0"):
        raise DatasetValidationError("Supplier unit costs must be positive.")
    if _scalar(connection, "SELECT COUNT(*) FROM products p WHERE NOT EXISTS (SELECT 1 FROM supplier_products sp WHERE sp.product_id = p.product_id)"):
        raise DatasetValidationError("Every product requires a supplier.")
    if _scalar(connection, "SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM customer_segments cs WHERE cs.segment_id = c.segment_id)"):
        raise DatasetValidationError("Every customer requires a valid segment.")
    if _scalar(connection, "SELECT COUNT(*) FROM (SELECT product_id FROM supplier_products GROUP BY product_id HAVING SUM(is_preferred) != 1)"):
        raise DatasetValidationError("Every product requires exactly one preferred supplier.")
    duplicate_checks = ("stores.code", "warehouses.code", "employees.employee_code", "products.sku", "suppliers.supplier_code", "customers.customer_code")
    for table_column in duplicate_checks:
        table, column = table_column.split(".")
        if _scalar(connection, f"SELECT COUNT(*) FROM (SELECT {column} FROM {table} GROUP BY {column} HAVING COUNT(*) > 1)"):
            raise DatasetValidationError(f"Duplicate values found for {table_column}.")
    return ["Foreign keys valid", "Product pricing valid", "Every product has suppliers", "Preferred supplier assignments valid", "Customer segments valid"]
