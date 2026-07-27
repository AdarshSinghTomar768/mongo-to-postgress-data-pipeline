# Mongo to PostgreSQL Data Pipeline

A batch ETL pipeline that reads MongoDB JSONL exports, validates and cleans customer and order records, loads them into PostgreSQL, and exposes a REST API for querying order data.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Pipeline](#running-the-pipeline)
- [Running the API](#running-the-api)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [SQL Schema](#sql-schema)
- [Validation Rules](#validation-rules)
- [Duplicate Handling](#duplicate-handling)
- [Project Structure](#project-structure)
- [Assumptions and Trade-offs](#assumptions-and-trade-offs)

---

## Architecture Overview

```
data/customers.jsonl ──┐
                       ├──> ETL Pipeline ──> PostgreSQL ──> FastAPI ──> GET /orders
data/orders.jsonl ─────┘
```

1. **Parser** -- Reads JSONL files and converts MongoDB Extended JSON (`$oid`, `$date`, `$numberDecimal`) into native Python types.
2. **Validator** -- Checks each record for required fields, valid types, and business rules.
3. **Loader** -- Deduplicates and inserts valid records into PostgreSQL. Invalid records are stored in a `rejected_records` table with rejection reasons.
4. **API** -- Serves order data with embedded customer info, filtering, and pagination.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| PostgreSQL | 12+ |
| pip | latest |

---

## Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd mongo-to-postgres-data-pipeline

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database
createdb order_db

# 5. Configure environment variables
export DATABASE_URL=postgresql://localhost:5432/order_db
```

Or create a `.env` file in the project root:

```
DATABASE_URL=postgresql://localhost:5432/order_db
```

---

## Running the Pipeline

```bash
python -m app.pipeline
```

**What it does:**

1. Creates the required tables (`customers`, `orders`, `rejected_records`) if they don't exist
2. Reads `data/customers.jsonl` (5,008 records) and `data/orders.jsonl` (15,020 records)
3. Validates each record against business rules
4. Inserts valid records into PostgreSQL
5. Stores rejected records with source type, source ID, and rejection reason
6. Prints summary statistics

**Expected output:**

```
==================================================
Starting ETL Pipeline
==================================================
Loading customers...
...
Read: 5008
Valid: 5004
Rejected: 4
Pending inserts: 0
Loading orders...
Orders loaded successfully.
==================================================
ETL Pipeline Completed Successfully
==================================================
```

> The pipeline is **idempotent** -- re-running it will not create duplicate accepted or rejected rows.

---

## Running the API

```bash
uvicorn app.api:app --reload
```

The API starts at `http://localhost:8000`.

- **Interactive docs (Swagger):** http://localhost:8000/docs
- **Alternative docs (ReDoc):** http://localhost:8000/redoc

---

## API Reference

### `GET /orders`

Returns orders with embedded customer data and pagination metadata.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `order_date` | `YYYY-MM-DD` | No | Filter by UTC date |
| `customer_id` | `string` | No | Exact match on MongoDB ObjectId |
| `email` | `string` | No | Case-insensitive customer email match |
| `status` | `string` | No | Exact match: `completed`, `pending`, or `cancelled` |
| `limit` | `integer` | No | Results per page (default: `50`, max: `100`) |
| `offset` | `integer` | No | Pagination offset (default: `0`) |

Multiple filters are combined with **AND**.

**Example requests:**

```bash
# All orders
curl http://localhost:8000/orders

# Filter by status and email
curl "http://localhost:8000/orders?status=completed&email=alice@example.com"

# Filter by date with pagination
curl "http://localhost:8000/orders?order_date=2024-06-15&limit=10&offset=0"
```

**Response:**

```json
{
  "data": [
    {
      "mongo_id": "66b000020000000000000001",
      "customer_mongo_id": "65a000010000000000001207",
      "amount": 557.80,
      "status": "cancelled",
      "source_platform": "web_app",
      "order_timestamp": "2025-08-21T01:34:50",
      "purchase_city": "Berlin",
      "purchase_state": "Berlin",
      "purchase_country": "DE",
      "customer": {
        "mongo_id": "65a000010000000000001207",
        "name": "Ishaan Iyer",
        "email": "ishaan.iyer4615@example.com",
        "city": "Berlin",
        "state": "Berlin",
        "country": "DE",
        "signup_date": "2024-10-07T05:30:00"
      }
    }
  ],
  "pagination": {
    "total": 12499,
    "limit": 50,
    "offset": 0,
    "next_offset": 50
  }
}
```

### `GET /customers`

Returns a paginated list of customers.

```bash
curl "http://localhost:8000/customers?limit=10&offset=0"
```

### `GET /customers/{mongo_id}`

Returns a single customer by their MongoDB ObjectId.

```bash
curl http://localhost:8000/customers/65a000010000000000001207
```

### `GET /orders/{mongo_id}`

Returns a single order by its MongoDB ObjectId.

```bash
curl http://localhost:8000/orders/66b000020000000000000001
```

### Error Responses

| Status Code | When |
|---|---|
| `400` | Invalid `order_date` format (not `YYYY-MM-DD`) |
| `404` | Customer or order not found |
| `422` | Invalid query parameters (e.g., `limit > 100`, negative `offset`) |

---

## Running Tests

```bash
pytest -v
```

**31 tests** across two test files:

| File | Tests | Coverage |
|---|---|---|
| `tests/test_validator.py` | 13 | Parser, customer validation, order validation |
| `tests/test_api.py` | 18 | Order filters, combined filters, pagination, error handling, customers |

Tests use an in-memory SQLite database -- no PostgreSQL instance required.

---

## SQL Schema

Full schema available in `sql/schema.sql`. Tables are also auto-created by the pipeline via SQLAlchemy ORM.

**Tables:**

| Table | Purpose |
|---|---|
| `customers` | Cleaned customer records with MongoDB ID mapping |
| `orders` | Cleaned order records with foreign key to customers |
| `rejected_records` | Invalid/duplicate records with rejection reason and raw data |

---

## Validation Rules

### Customers

A customer record is **rejected** if:

| Rule | Description |
|---|---|
| Missing `_id` | MongoDB ObjectId is required |
| Missing `name` | Customer name is required |
| Missing `email` | Email address is required |
| Invalid `email` | Must match `^[^@\s]+@[^@\s]+\.[^@\s]+$` |
| Missing `address` | Address with `city`, `state`, `country` is required |
| Missing `signup_date` | Signup date is required |
| Invalid `signup_date` | Must parse to a valid datetime |

### Orders

An order record is **rejected** if:

| Rule | Description |
|---|---|
| Missing `_id` | MongoDB ObjectId is required |
| Missing `customer_id` | Must reference an existing customer |
| Missing `amount` | Order amount is required |
| Invalid `amount` | Must be a positive decimal |
| Missing `status` | Order status is required |
| Invalid `status` | Must be one of: `completed`, `pending`, `cancelled` |
| Missing `source_platform` | Platform is required |
| Invalid `source_platform` | Must be one of: `android_app`, `ios_app`, `web_app` |
| Missing `order_timestamp` | Timestamp is required |
| Invalid `order_timestamp` | Must parse to a valid datetime |
| Missing `purchase_address` | Address with `city`, `state`, `country` is required |
| Unknown `customer_id` | Referenced customer must exist in `customers` table |

---

## Duplicate Handling

- **Detection:** Duplicates are identified by the `mongo_id` field, enforced by a unique constraint in PostgreSQL.
- **Rule:** If a customer or order with the same `mongo_id` already exists (in the database or in the current batch), the new record is rejected with reason `"Duplicate customer"` or `"Duplicate order"`.
- **Idempotency:** Re-running the pipeline produces identical results -- no duplicate accepted or rejected rows.
- **Rejected record deduplication:** The `rejected_records` table has a unique constraint on `(source_type, source_id, rejection_reason)` to prevent duplicate rejection entries.

---

## Project Structure

```
mongo-to-postgres-data-pipeline/
├── app/
│   ├── __init__.py
│   ├── api.py          # FastAPI application and endpoints
│   ├── config.py       # Environment variable loading
│   ├── database.py     # SQLAlchemy engine and session setup
│   ├── models.py       # ORM models (Customer, Order, RejectedRecord)
│   ├── parser.py       # MongoDB Extended JSON parser
│   ├── pipeline.py     # ETL pipeline orchestration
│   └── validator.py    # Record validation logic
├── data/
│   ├── customers.jsonl  # Source customer data (5,008 records)
│   └── orders.jsonl     # Source order data (15,020 records)
├── sql/
│   └── schema.sql       # SQL DDL statements
├── tests/
│   ├── conftest.py      # Test fixtures and database setup
│   ├── test_api.py      # API endpoint tests
│   └── test_validator.py # Validator and parser tests
├── .env                 # Environment configuration (not committed)
├── .gitignore
├── Readme.md
├── requirements.txt
└── candidate-assignment/
    └── ASSIGNMENT.md    # Original assignment specification
```

---

## Assumptions and Trade-offs

| Decision | Rationale |
|---|---|
| **Only `completed`, `pending`, `cancelled` statuses accepted** | ~2,500 records with `refunded` status and 1 with `shipped` are rejected as a deliberate data quality gate. |
| **No API authentication** | Out of scope per assignment requirements. |
| **SQLite for tests** | Tests use SQLite for speed and portability -- no running PostgreSQL required. |
| **Hardcoded file paths** | Pipeline reads from `data/customers.jsonl` and `data/orders.jsonl` relative to the project root. |
| **No Docker** | Simple, correct solution preferred over container infrastructure per assignment guidelines. |
