"""Integration tests for the empty reference SQLite schema."""

import sqlite3

import pytest

from scripts.create_database import connect_database, create_database

EXPECTED_TABLES = {
    "stores", "warehouses", "employees", "categories", "brands", "products", "suppliers",
    "supplier_products", "customer_segments", "customers", "promotions", "promotion_products",
    "sales_orders", "sales_order_items", "payments", "returns", "return_items", "purchase_orders",
    "purchase_order_items", "inventory", "inventory_movements", "sales_targets",
}


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "business_demo.sqlite"
    create_database(path)
    return path


def test_creates_exactly_the_expected_business_tables(database_path):
    with connect_database(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        assert tables == EXPECTED_TABLES
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_foreign_key_enforcement_rejects_an_invalid_store(database_path):
    with connect_database(database_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO employees (employee_code, store_id, first_name, last_name, position, hire_date, status) "
            "VALUES ('EMP-001', 999, 'Ana', 'Paz', 'Seller', '2026-01-01', 'ACTIVE')"
        )


def test_quantity_constraints_reject_zero_or_negative_values(database_path):
    with connect_database(database_path) as connection:
        connection.executescript(
            """
            INSERT INTO stores (store_id, code, name, city, region, status)
            VALUES (1, 'ST-001', 'Central', 'Lima', 'Lima', 'ACTIVE');
            INSERT INTO employees
                (employee_id, employee_code, store_id, first_name, last_name, position, hire_date, status)
            VALUES (1, 'EMP-001', 1, 'Ana', 'Paz', 'Seller', '2026-01-01', 'ACTIVE');
            INSERT INTO categories (category_id, name) VALUES (1, 'General');
            INSERT INTO brands (brand_id, name) VALUES (1, 'Marca');
            INSERT INTO products
                (product_id, sku, name, category_id, brand_id, base_price_cents, base_cost_cents, status)
            VALUES (1, 'SKU-001', 'Producto', 1, 1, 100, 80, 'ACTIVE');
            INSERT INTO sales_orders
                (order_id, order_number, order_date, store_id, seller_id, channel, status,
                 subtotal_cents, total_cents)
            VALUES (1, 'SO-001', '2026-01-01', 1, 1, 'STORE', 'COMPLETED', 100, 100);
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sales_order_items "
                "(order_id, product_id, quantity, unit_price_cents, unit_cost_cents) "
                "VALUES (1, 1, 0, 100, 80)"
            )
