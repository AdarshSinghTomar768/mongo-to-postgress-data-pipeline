# Data Engineering Intern Take-Home Assignment

## Scenario

Our application stores customers and orders in MongoDB. Your job is to clean
the exported data, load it into a relational database, and provide an API for
reading order data.

## Source data

You are given:

- `data/customers.jsonl` — about 5,000 customers
- `data/orders.jsonl` — about 15,000 orders

JSONL means that each line is one JSON document. The files use MongoDB Extended
JSON:

- ObjectId: `{"$oid": "..."}`
- Date: `{"$date": "..."}`
- Decimal: `{"$numberDecimal": "..."}`

Customers have an `address` containing `city`, `state`, and `country`. Orders
have a separate `purchase_address` with the same fields. Orders also have a
`source_platform`: `android_app`, `ios_app`, or `web_app`.

The files contain some invalid and duplicate records. Finding and handling them
is part of the assignment.

## Time and technology

Please submit the assignment before the deadline which would be have communicated by HR Manager/Hiring Manager, If you run out of time, submit what you have and describe what you would do next.

Use **Python or Go**. You may use any suitable libraries or API framework.
Choose **PostgreSQL or MySQL** as the destination database; supporting both is
not required.

## Your task

### Part 1 — Data pipeline

Build a batch pipeline that:

1. Reads both JSONL files and parses the MongoDB Extended JSON values.
2. Validates and cleans customer and order records.
3. Handles duplicates using a rule that you document.
4. Loads accepted records into PostgreSQL or MySQL.
5. Stores rejected records in a database table with:
   - source type (`customer` or `order`);
   - source ID, when available;
   - rejection reason; and
   - the original record or enough data to investigate it.
6. Can be run again with the same files without creating duplicate accepted or
   rejected rows.

Create relational customer and order tables with suitable types, keys, and a
customer/order relationship. Preserve customer addresses and order
purchase-time addresses separately.

At minimum, consider required fields, ObjectIds, dates, amounts, statuses,
addresses, source platforms, duplicates, and orders that reference unknown
customers. Do not silently drop invalid records.

### Part 2 — Order API

Build an HTTP API that reads from the relational database created in Part 1.
It must not read from the JSONL files.

Implement:

```text
GET /orders
```

Each order in the response must include its customer data.

Support these optional filters:

| Query parameter | Behaviour |
| --- | --- |
| `order_date` | Match a UTC date in `YYYY-MM-DD` format. |
| `customer_id` | Exact match on the original MongoDB customer ObjectId. |
| `email` | Exact, case-insensitive customer email match. |
| `status` | Exact order-status match. |

The endpoint must work with no filter, one filter, or any combination of
filters. Combine multiple filters using **AND**.

Add `limit` and `offset` pagination. The default limit is 50 and the maximum is
100. Use stable ordering and include enough pagination information in the JSON
response to request the next page.

Return HTTP `400` for invalid filter or pagination values.

## What to submit

Submit a link to a **public GitHub repository** containing your complete
solution. The repository must be accessible without requesting permission.
Commit all required code and documentation to the repository's default branch.

The repository must include:

- Pipeline and API source code in Python or Go
- SQL schema or migration files
- Dependency file, such as `requirements.txt`, `pyproject.toml`, or `go.mod`
- At least three useful automated tests across both parts, including:
  - a pipeline validation or transformation test; and
  - an API test using at least two filters together
- `README.md` with:
  - setup and database requirements;
  - the command to run the pipeline;
  - the command to start the API;
  - API response format and example requests;
  - the command to run tests;
  - validation and duplicate-handling rules;
  - assumptions, trade-offs, and unfinished work
- `AI_USAGE.md` stating whether you used AI tools and what you used them for

Use environment variables or configuration for database credentials. Do not
commit passwords, secret keys, local environment files, or other credentials.

## Out of scope

You do not need to build scheduling, cloud infrastructure, orchestration,
analytics tables, dashboards, a user interface, API authentication, API write
operations, or deployment. Docker is optional and receives no extra credit.

Prefer a simple, correct solution over unnecessary infrastructure.

## Follow-up discussion

A follow-up discussion will be based on your submitted assignment.
