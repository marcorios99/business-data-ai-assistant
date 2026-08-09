CREATE TABLE IF NOT EXISTS customer_segments (
    segment_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_code TEXT NOT NULL UNIQUE,
    segment_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    tax_id TEXT UNIQUE,
    city TEXT,
    region TEXT,
    registration_date TEXT NOT NULL,
    credit_limit_cents INTEGER NOT NULL DEFAULT 0 CHECK (credit_limit_cents >= 0),
    status TEXT NOT NULL,
    FOREIGN KEY (segment_id) REFERENCES customer_segments(segment_id)
);
