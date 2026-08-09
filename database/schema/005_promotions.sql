CREATE TABLE IF NOT EXISTS promotions (
    promotion_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    promotion_type TEXT NOT NULL CHECK (promotion_type IN ('PERCENTAGE', 'FIXED_AMOUNT')),
    discount_percent REAL,
    discount_amount_cents INTEGER,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL,
    CHECK (start_date <= end_date),
    CHECK (
        (promotion_type = 'PERCENTAGE' AND discount_percent > 0 AND discount_percent <= 100
            AND discount_amount_cents IS NULL)
        OR (promotion_type = 'FIXED_AMOUNT' AND discount_amount_cents > 0
            AND discount_percent IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS promotion_products (
    promotion_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    PRIMARY KEY (promotion_id, product_id),
    FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
