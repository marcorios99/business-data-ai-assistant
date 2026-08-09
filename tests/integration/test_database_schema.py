"""Integration tests for the empty reference SQLite schema."""

import sqlite3

import pytest

from scripts import create_database as database_creator
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


def seed_sales_prerequisites(connection):
    """Insert the minimum valid data required by inventory and sales item tests."""
    connection.executescript(
        """
        INSERT INTO stores (store_id, code, name, city, region, status)
        VALUES (1, 'ST-001', 'Central', 'Lima', 'Lima', 'ACTIVE');
        INSERT INTO warehouses (warehouse_id, code, name, city, region, status)
        VALUES (1, 'WH-001', 'Central', 'Lima', 'Lima', 'ACTIVE');
        INSERT INTO employees
            (employee_id, employee_code, store_id, first_name, last_name, position, hire_date, status)
        VALUES (1, 'EMP-001', 1, 'Ana', 'Paz', 'Seller', '2026-01-01', 'ACTIVE');
        INSERT INTO categories (category_id, name) VALUES (1, 'General');
        INSERT INTO brands (brand_id, name) VALUES (1, 'Marca');
        INSERT INTO products
            (product_id, sku, name, category_id, brand_id, base_price_cents, base_cost_cents, status)
        VALUES
            (1, 'SKU-001', 'Producto uno', 1, 1, 100, 80, 'ACTIVE'),
            (2, 'SKU-002', 'Producto dos', 1, 1, 200, 150, 'ACTIVE');
        INSERT INTO sales_orders
            (order_id, order_number, order_date, store_id, seller_id, channel, status,
             subtotal_cents, total_cents)
        VALUES (1, 'SO-001', '2026-01-01', 1, 1, 'STORE', 'COMPLETED', 100, 100);
        """
    )


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
        seed_sales_prerequisites(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sales_order_items "
                "(order_id, product_id, quantity, unit_price_cents, unit_cost_cents) "
                "VALUES (1, 1, 0, 100, 80)"
            )


def test_inventory_reservations_cannot_exceed_available_stock(database_path):
    with connect_database(database_path) as connection:
        seed_sales_prerequisites(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO inventory "
                "(warehouse_id, product_id, quantity_on_hand, quantity_reserved, updated_at) "
                "VALUES (1, 1, 5, 6, '2026-01-01T00:00:00Z')"
            )


def test_promotion_must_apply_to_the_sales_item_product(database_path):
    with connect_database(database_path) as connection:
        seed_sales_prerequisites(connection)
        connection.execute(
            "INSERT INTO promotions "
            "(promotion_id, code, name, promotion_type, discount_percent, start_date, end_date, status) "
            "VALUES (1, 'PROMO-001', 'Oferta', 'PERCENTAGE', 10, '2026-01-01', '2026-01-31', 'ACTIVE')"
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sales_order_items "
                "(order_id, product_id, promotion_id, quantity, unit_price_cents, unit_cost_cents) "
                "VALUES (1, 1, 1, 1, 100, 80)"
            )


def test_valid_product_promotion_can_be_used_by_a_sales_item(database_path):
    with connect_database(database_path) as connection:
        seed_sales_prerequisites(connection)
        connection.executescript(
            """
            INSERT INTO promotions
                (promotion_id, code, name, promotion_type, discount_percent, start_date, end_date, status)
            VALUES (1, 'PROMO-001', 'Oferta', 'PERCENTAGE', 10, '2026-01-01', '2026-01-31', 'ACTIVE');
            INSERT INTO promotion_products (promotion_id, product_id) VALUES (1, 1);
            """
        )

        connection.execute(
            "INSERT INTO sales_order_items "
            "(order_id, product_id, promotion_id, quantity, unit_price_cents, unit_cost_cents) "
            "VALUES (1, 1, 1, 1, 100, 80)"
        )
        assert connection.execute("SELECT COUNT(*) FROM sales_order_items").fetchone()[0] == 1


def test_failed_schema_creation_removes_the_incomplete_database(tmp_path, monkeypatch):
    invalid_schema = tmp_path / "invalid_schema.sql"
    invalid_schema.write_text("CREATE TABLE broken (;", encoding="utf-8")
    incomplete_path = tmp_path / "incomplete.sqlite"
    monkeypatch.setattr(database_creator, "schema_files", lambda: [invalid_schema])

    with pytest.raises(RuntimeError, match="Failed to create database"):
        create_database(incomplete_path)

    assert not incomplete_path.exists()
