CREATE TABLE IF NOT EXISTS returns (
    return_id INTEGER PRIMARY KEY,
    return_number TEXT NOT NULL UNIQUE,
    order_id INTEGER NOT NULL,
    return_date TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id)
);

CREATE TABLE IF NOT EXISTS return_items (
    return_item_id INTEGER PRIMARY KEY,
    return_id INTEGER NOT NULL,
    order_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    refund_amount_cents INTEGER NOT NULL CHECK (refund_amount_cents >= 0),
    inventory_disposition TEXT NOT NULL,
    FOREIGN KEY (return_id) REFERENCES returns(return_id),
    FOREIGN KEY (order_item_id) REFERENCES sales_order_items(order_item_id)
);
