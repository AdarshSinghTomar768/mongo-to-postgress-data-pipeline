# AI Usage

Yes, I used AI tools (OpenCode with the big-pickle model) to assist with this assignment.

## What I used AI for

- **Project exploration**: AI scanned the entire codebase to identify what was already implemented and what was missing relative to the assignment requirements.
- **API redesign**: AI rewrote `app/api.py` to add the required filters (`order_date`, `customer_id`, `email`, `status`), include customer data in order responses, add pagination metadata, enforce the limit cap of 100, and return proper HTTP 400/422 errors.
- **Pipeline bug fix**: AI identified and fixed the `session.rollback()` bug in `reject_record()` that could discard valid buffered inserts when an IntegrityError occurred on a duplicate rejected record.
- **Test suite**: AI generated the full test suite (`tests/conftest.py`, `tests/test_validator.py`, `tests/test_api.py`) including pipeline validation tests and API tests with combined filters.
- **Documentation**: AI drafted the README and this file.
- **SQL schema**: AI generated `sql/schema.sql` from the existing ORM models.
