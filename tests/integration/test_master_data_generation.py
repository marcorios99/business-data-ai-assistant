"""Behavioral tests for deterministic master-data generation."""

from scripts.create_database import connect_database, create_database
from scripts.dataset.config import DatasetScale, get_dataset_config
from scripts.dataset.generator import generate_master_data
from scripts.dataset.validation import validate_master_data


def generate_demo(path, seed=2026):
    create_database(path)
    config = get_dataset_config(DatasetScale.DEMO)
    with connect_database(path) as connection:
        generate_master_data(connection, config, seed)
        return validate_master_data(connection, config)


def table_snapshot(path):
    tables = ("stores", "employees", "products", "supplier_products", "customers")
    with connect_database(path) as connection:
        return {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall() for table in tables}


def test_demo_master_data_generation_is_valid(tmp_path):
    results = generate_demo(tmp_path / "demo.sqlite")
    assert "Foreign keys valid" in results


def test_same_seed_generates_identical_master_data(tmp_path):
    first, second = tmp_path / "first.sqlite", tmp_path / "second.sqlite"
    generate_demo(first, 2026)
    generate_demo(second, 2026)
    assert table_snapshot(first) == table_snapshot(second)


def test_different_seed_changes_master_data(tmp_path):
    first, second = tmp_path / "first.sqlite", tmp_path / "second.sqlite"
    generate_demo(first, 2026)
    generate_demo(second, 2027)
    assert table_snapshot(first)["products"] != table_snapshot(second)["products"]


def test_demo_counts_and_master_data_invariants(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    config = get_dataset_config("demo")
    with connect_database(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == config.customers
        assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == config.products
        assert connection.execute("SELECT COUNT(*) FROM supplier_products GROUP BY product_id HAVING SUM(is_preferred) != 1").fetchall() == []
        assert connection.execute("SELECT COUNT(*) FROM products WHERE base_cost_cents >= base_price_cents").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
