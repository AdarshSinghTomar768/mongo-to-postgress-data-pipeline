import json
from datetime import datetime
from decimal import Decimal

import pytest

from app.parser import parse_extended_json, load_jsonl
from app.validator import validate_customer, validate_order


class TestParseExtendedJson:
    def test_parse_oid(self):
        result = parse_extended_json({"$oid": "507f1f77bcf86cd799439011"})
        assert result == "507f1f77bcf86cd799439011"

    def test_parse_date(self):
        result = parse_extended_json({"$date": "2024-01-15T10:30:00Z"})
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_decimal(self):
        result = parse_extended_json({"$numberDecimal": "199.99"})
        assert isinstance(result, Decimal)
        assert result == Decimal("199.99")

    def test_parse_nested(self):
        doc = {
            "_id": {"$oid": "abc123"},
            "amount": {"$numberDecimal": "42.50"},
            "items": [{"name": "item1"}],
        }
        result = parse_extended_json(doc)
        assert result["_id"] == "abc123"
        assert result["amount"] == Decimal("42.50")
        assert result["items"][0]["name"] == "item1"


class TestValidateCustomer:
    def test_valid_customer(self):
        customer = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "John Doe",
            "email": "john@example.com",
            "address": {"city": "NYC", "state": "NY", "country": "US"},
            "signup_date": datetime(2024, 1, 1),
        }
        valid, reason = validate_customer(customer)
        assert valid is True
        assert reason is None

    def test_missing_required_field(self):
        customer = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "john@example.com",
            "address": {"city": "NYC", "state": "NY", "country": "US"},
            "signup_date": datetime(2024, 1, 1),
        }
        valid, reason = validate_customer(customer)
        assert valid is False
        assert "name" in reason

    def test_invalid_email(self):
        customer = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "John",
            "email": "not-an-email",
            "address": {"city": "NYC", "state": "NY", "country": "US"},
            "signup_date": datetime(2024, 1, 1),
        }
        valid, reason = validate_customer(customer)
        assert valid is False
        assert "email" in reason

    def test_missing_address_field(self):
        customer = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "John",
            "email": "john@example.com",
            "address": {"city": "NYC"},
            "signup_date": datetime(2024, 1, 1),
        }
        valid, reason = validate_customer(customer)
        assert valid is False
        assert "state" in reason


class TestValidateOrder:
    def _make_order(self, **overrides):
        order = {
            "_id": "507f1f77bcf86cd799439022",
            "customer_id": "507f1f77bcf86cd799439011",
            "amount": Decimal("99.99"),
            "status": "completed",
            "source_platform": "web_app",
            "order_timestamp": datetime(2024, 6, 1, 12, 0),
            "purchase_address": {"city": "LA", "state": "CA", "country": "US"},
        }
        order.update(overrides)
        return order

    def test_valid_order(self):
        valid, reason = validate_order(self._make_order())
        assert valid is True
        assert reason is None

    def test_invalid_status(self):
        valid, reason = validate_order(self._make_order(status="refunded"))
        assert valid is False
        assert "status" in reason

    def test_invalid_platform(self):
        valid, reason = validate_order(self._make_order(source_platform="desktop"))
        assert valid is False
        assert "platform" in reason

    def test_negative_amount(self):
        valid, reason = validate_order(self._make_order(amount=Decimal("-10")))
        assert valid is False
        assert "positive" in reason

    def test_missing_required_field(self):
        order = self._make_order()
        del order["customer_id"]
        valid, reason = validate_order(order)
        assert valid is False
        assert "customer_id" in reason
