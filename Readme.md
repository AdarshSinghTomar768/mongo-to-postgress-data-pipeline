# Mongo to PostgreSQL Data Pipeline

Batch ETL pipeline that reads MongoDB JSONL exports, validates and cleans customer and order records, loads them into PostgreSQL, and exposes an HTTP API for querying order data.

## Setup and Requirements

- Python 3.11+
- PostgreSQL running locally (default: `localhost:5432`)
- A database named `order_db` (or set `DATABASE_URL` in `.env`)

```bash
# Create database
createdb order_db

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # or create .env with:
# DATABASE_URL=postgresql://user:password@localhost:5432/order_db
```

## Running the Pipeline

```bash
python -m app.pipeline
```

This will:
1. Create the required tables (`customers`, `orders`, `rejected_records`) if they don't exist
2. Read `data/customers.jsonl` and `data/orders.jsonl`
3. Validate records, reject invalid ones, and insert valid ones into PostgreSQL
4. Print summary statistics

The pipeline is **idempotent** -- re-running it will not create duplicate accepted or rejected rows.

## Running the API

```bash
uvicorn app.api:app --reload
```

The API will be available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## API Response Format and Example Requests

### GET /orders

Returns orders with embedded customer data and pagination metadata.

```
GET /orders
GET /orders?status=completed&email=alice@example.com
GET /orders?order_date=2024-06-15&limit=10&offset=0
```

**Query Parameters:**

| Parameter | Description |
|---|---|
| `order_date` | Match a UTC date in `YYYY-MM-DD` format |
| `customer_id` | Exact match on the original MongoDB customer ObjectId |
| `email` | Exact, case-insensitive customer email match |
| `status` | Exact order-status match (`completed`, `pending`, `cancelled`) |
| `limit` | Number of results (default: 50, max: 100) |
| `offset` | Pagination offset (default: 0) |

**Response example:**

```json
{
  "data": [
    {
      "mongo_id": "507f1f77bcf86cd799439022",
      "customer_mongo_id": "507f1f77bcf86cd799439011",
      "amount": 99.99,
      "status": "completed",
      "source_platform": "web_app",
      "order_timestamp": "2024-06-15T10:00:00",
      "purchase_city": "New York",
      "purchase_state": "NY",
      "purchase_country": "US",
      "customer": {
        "mongo_id": "507f1f77bcf86cd799439011",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "signup_date": "2024-01-15T00:00:00"
      }
    }
  ],
  "pagination": {
    "total": 15000,
    "limit": 50,
    "offset": 0,
    "next_offset": 50
  }
}
```

### GET /customers

```
GET /customers?limit=10&offset=0
```

### GET /customers/{mongo_id}

Returns a single customer by their MongoDB ObjectId.

### GET /orders/{mongo_id}

Returns a single order by its MongoDB ObjectId.

## Running Tests

```bash
pytest -v
```

## Validation and Duplicate-Handling Rules

### Customer Validation

A customer record is rejected if it is missing any of: `_id`, `name`, `email`, `address` (with `city`, `state`, `country`), `signup_date`. Additional checks:
- `name` must not be blank
- `email` must match a basic email pattern (`[^@\s]+@[^@\s]+\.[^@\s]+`)
- `signup_date` must parse to a valid datetime

### Order Validation

An order record is rejected if it is missing any of: `_id`, `customer_id`, `amount`, `status`, `source_platform`, `order_timestamp`, `purchase_address` (with `city`, `state`, `country`). Additional checks:
- `amount` must be a positive decimal
- `status` must be one of: `completed`, `pending`, `cancelled`
- `source_platform` must be one of: `android_app`, `ios_app`, `web_app`
- `order_timestamp` must parse to a valid datetime
- `customer_id` must reference an existing customer in the `customers` table

### Duplicate Handling

Duplicates are detected by the `mongo_id` field (unique constraint). If a customer or order with the same `mongo_id` already exists in the database, the new record is rejected with reason "Duplicate customer" or "Duplicate order". This ensures idempotency -- re-running the pipeline does not create duplicate rows.

Rejected records are also deduplicated by a unique constraint on `(source_type, source_id, rejection_reason)`.

## SQL Schema

The full schema is in `sql/schema.sql`. Tables are also auto-created by the pipeline via SQLAlchemy ORM.

## Assumptions, Trade-offs, and Unfinished Work

- **Status values**: The validator only accepts `completed`, `pending`, `cancelled`. The test data contains ~2,500 records with status `refunded` and 1 with `shipped`, which are rejected. This is a deliberate data quality gate.
- **No authentication**: The API has no auth layer, as specified in the assignment.
- **SQLite in tests**: Tests use an in-memory SQLite database for speed and portability, avoiding the need for a running PostgreSQL instance.
- **Hardcoded file paths**: The pipeline reads from `data/customers.jsonl` and `data/orders.jsonl` relative to the project root.
