CREATE TABLE IF NOT EXISTS sales_targets (
    target_id INTEGER PRIMARY KEY,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    store_id INTEGER,
    employee_id INTEGER,
    metric TEXT NOT NULL,
    target_amount_cents INTEGER NOT NULL CHECK (target_amount_cents >= 0),
    CHECK (period_start <= period_end),
    CHECK (store_id IS NOT NULL OR employee_id IS NOT NULL),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
