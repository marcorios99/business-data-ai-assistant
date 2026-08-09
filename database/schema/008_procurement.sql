CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_order_id INTEGER PRIMARY KEY,
    purchase_order_number TEXT NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    expected_date TEXT,
    received_date TEXT,
    status TEXT NOT NULL,
    currency_code TEXT NOT NULL DEFAULT 'PEN',
    subtotal_cents INTEGER NOT NULL CHECK (subtotal_cents >= 0),
    tax_cents INTEGER NOT NULL DEFAULT 0 CHECK (tax_cents >= 0),
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
    purchase_order_item_id INTEGER PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    quantity_received INTEGER NOT NULL DEFAULT 0
        CHECK (quantity_received >= 0 AND quantity_received <= quantity_ordered),
    unit_cost_cents INTEGER NOT NULL CHECK (unit_cost_cents >= 0),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(purchase_order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
