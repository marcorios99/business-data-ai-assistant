CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY,
    supplier_code TEXT NOT NULL UNIQUE,
    legal_name TEXT NOT NULL,
    city TEXT,
    region TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_products (
    supplier_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    supplier_sku TEXT,
    unit_cost_cents INTEGER NOT NULL CHECK (unit_cost_cents >= 0),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 0 CHECK (is_preferred IN (0, 1)),
    PRIMARY KEY (supplier_id, product_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
