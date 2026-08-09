"""Behavioral tests for deterministic master-data generation."""

from dataclasses import replace
from datetime import date

import pytest

from scripts import generate_dataset as dataset_cli
from scripts.create_database import connect_database, create_database
from scripts.dataset import config as dataset_config
from scripts.dataset.config import DatasetScale, get_dataset_config, validate_all_configurations
from scripts.dataset.generator import generate_master_data
from scripts.dataset.master_data import CATEGORIES
from scripts.dataset.patterns import SUPPLIER_PROFILES, supplier_profile
from scripts.dataset.validation import (
    DatasetValidationError,
    validate_master_data,
    validate_procurement_and_inventory,
)


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


def test_all_scales_have_sufficient_static_vocabulary():
    validate_all_configurations()


def test_master_dates_do_not_exceed_dataset_end_date(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    end_date = get_dataset_config("demo").dataset_end_date
    with connect_database(path) as connection:
        for table, column in (("stores", "opened_on"), ("employees", "hire_date"), ("customers", "registration_date")):
            latest = connection.execute(f"SELECT MAX({column}) FROM {table}").fetchone()[0]
            assert date.fromisoformat(latest) <= end_date


def test_every_store_has_a_manager(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    with connect_database(path) as connection:
        stores_without_manager = connection.execute(
            "SELECT s.store_id FROM stores s LEFT JOIN employees e "
            "ON e.store_id = s.store_id AND e.position = 'Store Manager' "
            "WHERE e.employee_id IS NULL"
        ).fetchall()
    assert stores_without_manager == []


def test_demo_categories_include_each_product_type(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    with connect_database(path) as connection:
        for category_id, (_, product_types, _) in enumerate(CATEGORIES[:10], 1):
            names = [row[0] for row in connection.execute("SELECT name FROM products WHERE category_id = ?", (category_id,))]
            for product_type in product_types:
                assert any(f" {product_type} Series " in name for name in names)


def test_supplier_profile_ranges_are_consistent(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    with connect_database(path) as connection:
        relationships = connection.execute(
            "SELECT supplier_id, lead_time_days FROM supplier_products"
        ).fetchall()
    for supplier_id, lead_time_days in relationships:
        _, lead_time_range = SUPPLIER_PROFILES[supplier_profile(supplier_id)]
        assert lead_time_range[0] <= lead_time_days <= lead_time_range[1]

    with connect_database(path) as connection:
        cost_rows = connection.execute(
            "SELECT sp.supplier_id, sp.unit_cost_cents, p.base_cost_cents "
            "FROM supplier_products sp JOIN products p ON p.product_id = sp.product_id"
        ).fetchall()
    profile_costs = {profile: [] for profile in SUPPLIER_PROFILES}
    for supplier_id, unit_cost, base_cost in cost_rows:
        profile_costs[supplier_profile(supplier_id)].append(unit_cost / base_cost)
    averages = {profile: sum(costs) / len(costs) for profile, costs in profile_costs.items()}
    assert averages["VALUE"] < averages["BALANCED"] < averages["FAST"]


def test_business_customers_receive_business_names(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_demo(path)
    with connect_database(path) as connection:
        names = connection.execute("SELECT name FROM customers WHERE segment_id > 1").fetchall()
    assert names
    assert all("SAC" in name for (name,) in names)


def test_failed_validation_removes_new_dataset_file(tmp_path, monkeypatch):
    path = tmp_path / "invalid.sqlite"
    monkeypatch.setattr(dataset_cli, "validate_master_data", lambda *_: (_ for _ in ()).throw(ValueError("invalid")))

    with pytest.raises(ValueError, match="invalid"):
        dataset_cli.generate_dataset(path, "demo", 2026)

    assert not path.exists()


def generate_procurement_demo(path, seed=2026):
    original = dataset_config.CONFIGURATIONS[DatasetScale.DEMO]
    dataset_config.CONFIGURATIONS[DatasetScale.DEMO] = replace(original, sales_orders=200)
    try:
        return dataset_cli.generate_dataset(path, "demo", seed)
    finally:
        dataset_config.CONFIGURATIONS[DatasetScale.DEMO] = original


def test_demo_generation_includes_procurement_and_inventory(tmp_path):
    summary, validation_results = generate_procurement_demo(tmp_path / "demo.sqlite")
    assert summary["purchase_orders"] == get_dataset_config("demo").purchase_orders
    assert summary["purchase_items"] >= summary["purchase_orders"] * 3
    assert summary["initial_movements"] >= summary["products"]
    assert "Inventory ledger reconciles" in validation_results


def test_procurement_and_inventory_are_deterministic_by_seed(tmp_path):
    first, second = tmp_path / "first.sqlite", tmp_path / "second.sqlite"
    generate_procurement_demo(first, 2026)
    generate_procurement_demo(second, 2026)
    tables = ("purchase_orders", "purchase_order_items", "inventory_movements", "inventory")
    with connect_database(first) as first_connection, connect_database(second) as second_connection:
        for table in tables:
            assert first_connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall() == second_connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()


def test_every_product_has_initial_stock_and_inventory_reconciles(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_procurement_demo(path)
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM products p WHERE NOT EXISTS (SELECT 1 FROM inventory_movements im WHERE im.product_id = p.product_id AND im.movement_type = 'INITIAL')"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM inventory i WHERE i.quantity_on_hand != (SELECT SUM(quantity_delta) FROM inventory_movements im WHERE im.warehouse_id = i.warehouse_id AND im.product_id = i.product_id)"
        ).fetchone()[0] == 0


def test_purchase_receipts_match_suppliers_quantities_and_order_totals(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_procurement_demo(path)
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM purchase_order_items poi JOIN purchase_orders po ON po.purchase_order_id = poi.purchase_order_id LEFT JOIN supplier_products sp ON sp.supplier_id = po.supplier_id AND sp.product_id = poi.product_id WHERE sp.product_id IS NULL"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM purchase_order_items poi WHERE poi.quantity_received != COALESCE((SELECT SUM(quantity_delta) FROM inventory_movements im WHERE im.movement_type = 'PURCHASE' AND im.reference_id = poi.purchase_order_item_id), 0)"
        ).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM purchase_orders WHERE total_cents != subtotal_cents + tax_cents").fetchone()[0] == 0


def test_inventory_ledger_corruption_is_detected(tmp_path):
    path = tmp_path / "demo.sqlite"
    generate_procurement_demo(path)
    with connect_database(path) as connection:
        connection.execute("UPDATE inventory SET quantity_on_hand = quantity_on_hand + 1 WHERE rowid = 1")
        with pytest.raises(DatasetValidationError, match="Inventory projection"):
            validate_procurement_and_inventory(connection)


def test_sales_payments_promotions_and_ledger_are_valid(tmp_path):
    path = tmp_path / "demo.sqlite"
    summary, _ = generate_procurement_demo(path)
    assert summary["sales_orders"] == 200
    assert summary["payments"] == summary["sales_orders"]
    with connect_database(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM sales_orders so JOIN employees e ON e.employee_id = so.seller_id WHERE e.store_id != so.store_id").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM sales_order_items WHERE promotion_id IS NOT NULL").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM inventory WHERE quantity_on_hand < 0").fetchone()[0] == 0
