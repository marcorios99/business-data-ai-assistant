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


def validate_procurement_and_inventory(
    connection: sqlite3.Connection, config: DatasetConfig | None = None
) -> list[str]:
    """Validate purchase, receipt, ledger, and inventory-projection invariants."""
    checks = (
        ("SELECT COUNT(*) FROM purchase_order_items WHERE quantity_ordered <= 0 OR quantity_received < 0 OR quantity_received > quantity_ordered", "Purchase quantities are invalid."),
        ("SELECT COUNT(*) FROM purchase_orders WHERE total_cents != subtotal_cents + tax_cents", "Purchase totals do not reconcile."),
        ("SELECT COUNT(*) FROM purchase_orders po WHERE po.subtotal_cents != (SELECT COALESCE(SUM(poi.quantity_ordered * poi.unit_cost_cents), 0) FROM purchase_order_items poi WHERE poi.purchase_order_id = po.purchase_order_id) OR po.tax_cents != ((po.subtotal_cents * 18 + 50) / 100)", "Purchase line totals do not reconcile."),
        ("SELECT COUNT(*) FROM purchase_orders WHERE expected_date < order_date OR (received_date IS NOT NULL AND received_date < order_date)", "Purchase dates are incoherent."),
        ("SELECT COUNT(*) FROM purchase_orders po WHERE po.status = 'RECEIVED' AND (po.received_date IS NULL OR EXISTS (SELECT 1 FROM purchase_order_items poi WHERE poi.purchase_order_id = po.purchase_order_id AND poi.quantity_received != poi.quantity_ordered))", "Received orders are inconsistent."),
        ("SELECT COUNT(*) FROM purchase_orders po WHERE po.status = 'OPEN' AND (po.received_date IS NOT NULL OR EXISTS (SELECT 1 FROM purchase_order_items poi WHERE poi.purchase_order_id = po.purchase_order_id AND poi.quantity_received != 0))", "Open orders are inconsistent."),
        ("SELECT COUNT(*) FROM purchase_orders po WHERE po.status = 'PARTIALLY_RECEIVED' AND (po.received_date IS NULL OR EXISTS (SELECT 1 FROM purchase_order_items poi WHERE poi.purchase_order_id = po.purchase_order_id AND NOT (poi.quantity_received > 0 AND poi.quantity_received < poi.quantity_ordered)))", "Partially received orders are inconsistent."),
        ("SELECT COUNT(*) FROM purchase_order_items poi JOIN purchase_orders po ON po.purchase_order_id = poi.purchase_order_id LEFT JOIN supplier_products sp ON sp.supplier_id = po.supplier_id AND sp.product_id = poi.product_id WHERE sp.product_id IS NULL", "Purchase item supplier mappings are invalid."),
        ("SELECT COUNT(*) FROM inventory_movements WHERE movement_type IN ('INITIAL', 'PURCHASE') AND quantity_delta <= 0", "Opening or purchase movements must be positive."),
        ("SELECT COUNT(*) FROM inventory_movements im LEFT JOIN purchase_order_items poi ON poi.purchase_order_item_id = im.reference_id WHERE im.movement_type = 'PURCHASE' AND (im.reference_type != 'PURCHASE_ORDER_ITEM' OR poi.purchase_order_item_id IS NULL)", "Purchase movement references are invalid."),
        ("SELECT COUNT(*) FROM purchase_order_items poi WHERE poi.quantity_received != COALESCE((SELECT SUM(im.quantity_delta) FROM inventory_movements im WHERE im.movement_type = 'PURCHASE' AND im.reference_id = poi.purchase_order_item_id), 0)", "Purchase receipts do not match ledger movements."),
        ("SELECT COUNT(*) FROM inventory i WHERE i.quantity_on_hand != (SELECT SUM(im.quantity_delta) FROM inventory_movements im WHERE im.warehouse_id = i.warehouse_id AND im.product_id = i.product_id) OR i.quantity_reserved != 0", "Inventory projection does not reconcile with its ledger."),
        ("SELECT COUNT(*) FROM inventory i WHERE NOT EXISTS (SELECT 1 FROM inventory_movements im WHERE im.warehouse_id = i.warehouse_id AND im.product_id = i.product_id)", "Inventory positions require ledger movements."),
        ("SELECT COUNT(*) FROM products p WHERE NOT EXISTS (SELECT 1 FROM inventory_movements im WHERE im.product_id = p.product_id AND im.movement_type = 'INITIAL')", "Every product requires initial stock."),
    )
    for query, message in checks:
        if _scalar(connection, query):
            raise DatasetValidationError(message)
    if config is not None and _scalar(
        connection,
        f"SELECT COUNT(*) FROM purchase_orders WHERE order_date > '{config.dataset_end_date.isoformat()}' OR expected_date > '{config.dataset_end_date.isoformat()}' OR received_date > '{config.dataset_end_date.isoformat()}'",
    ):
        raise DatasetValidationError("Purchase dates exceed the dataset period.")
    return ["Purchase orders valid", "Procurement totals reconcile", "Inventory ledger reconciles"]


def validate_sales(connection: sqlite3.Connection, config: DatasetConfig) -> list[str]:
    """Validate sales, payments, promotions, and historical inventory balances."""
    checks = (
        ("SELECT COUNT(*) FROM sales_orders so JOIN employees e ON e.employee_id = so.seller_id WHERE e.store_id != so.store_id", "Sales sellers must belong to their store."),
        ("SELECT COUNT(*) FROM sales_orders WHERE subtotal_cents - discount_cents + tax_cents != total_cents OR tax_cents != (((subtotal_cents - discount_cents) * 18 + 50) / 100)", "Sales totals do not reconcile."),
        ("SELECT COUNT(*) FROM sales_order_items soi JOIN sales_orders so ON so.order_id = soi.order_id WHERE soi.promotion_id IS NOT NULL AND (so.order_date NOT BETWEEN (SELECT start_date FROM promotions p WHERE p.promotion_id = soi.promotion_id) AND (SELECT end_date FROM promotions p WHERE p.promotion_id = soi.promotion_id))", "Promotion dates are invalid."),
        ("SELECT COUNT(*) FROM sales_order_items soi JOIN promotions p ON p.promotion_id = soi.promotion_id WHERE (p.promotion_type = 'PERCENTAGE' AND soi.discount_cents != (soi.quantity * soi.unit_price_cents * CAST(p.discount_percent AS INTEGER) / 100)) OR (p.promotion_type = 'FIXED_AMOUNT' AND soi.discount_cents != MIN(soi.quantity * soi.unit_price_cents, p.discount_amount_cents))", "Promotion discounts are invalid."),
        ("SELECT COUNT(*) FROM sales_order_items soi WHERE soi.quantity != -COALESCE((SELECT SUM(im.quantity_delta) FROM inventory_movements im WHERE im.movement_type = 'SALE' AND im.reference_id = soi.order_item_id), 0)", "Sale movements do not match items."),
        ("SELECT COUNT(*) FROM sales_orders so WHERE so.status = 'COMPLETED' AND so.total_cents != COALESCE((SELECT SUM(p.amount_cents) FROM payments p WHERE p.order_id = so.order_id AND p.status = 'SUCCESS'), 0)", "Payments do not reconcile."),
    )
    for query, message in checks:
        if _scalar(connection, query): raise DatasetValidationError(message)
    balances = {}
    for warehouse_id, product_id, delta in connection.execute("SELECT warehouse_id, product_id, quantity_delta FROM inventory_movements ORDER BY occurred_at, movement_id"):
        key = (warehouse_id, product_id); balances[key] = balances.get(key, 0) + delta
        if balances[key] < 0: raise DatasetValidationError("Inventory became negative historically.")
    return ["Sales totals and payments reconcile", "Promotions valid", "Historical inventory never negative"]
