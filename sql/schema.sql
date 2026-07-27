CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    mongo_id VARCHAR(24) NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR,
    signup_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    mongo_id VARCHAR(24) NOT NULL UNIQUE,
    customer_mongo_id VARCHAR(24) NOT NULL REFERENCES customers(mongo_id),
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR NOT NULL,
    source_platform VARCHAR NOT NULL,
    order_timestamp TIMESTAMP NOT NULL,
    purchase_city VARCHAR,
    purchase_state VARCHAR,
    purchase_country VARCHAR
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR NOT NULL,
    source_id VARCHAR,
    rejection_reason VARCHAR NOT NULL,
    raw_record JSONB NOT NULL,
    CONSTRAINT uq_rejected_record UNIQUE (source_type, source_id, rejection_reason)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_mongo_id ON orders(customer_mongo_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_timestamp ON orders(order_timestamp);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
