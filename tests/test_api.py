import pytest


class TestOrdersEndpoint:
    def test_get_orders_returns_all(self, client, seed_data):
        resp = client.get("/orders")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 3
        assert body["pagination"]["total"] == 3

    def test_orders_include_customer_data(self, client, seed_data):
        resp = client.get("/orders")
        body = resp.json()
        for order in body["data"]:
            assert "customer" in order
            assert order["customer"]["mongo_id"] == order["customer_mongo_id"]

    def test_filter_by_status(self, client, seed_data):
        resp = client.get("/orders?status=completed")
        body = resp.json()
        assert body["pagination"]["total"] == 1
        assert all(o["status"] == "completed" for o in body["data"])

    def test_filter_by_customer_id(self, client, seed_data):
        resp = client.get("/orders?customer_id=aaaa1111bbbb2222cccc3333")
        body = resp.json()
        assert body["pagination"]["total"] == 2
        assert all(o["customer_mongo_id"] == "aaaa1111bbbb2222cccc3333" for o in body["data"])

    def test_filter_by_email(self, client, seed_data):
        resp = client.get("/orders?email=alice@example.com")
        body = resp.json()
        assert body["pagination"]["total"] == 2

    def test_filter_by_email_case_insensitive(self, client, seed_data):
        resp = client.get("/orders?email=ALICE@EXAMPLE.COM")
        body = resp.json()
        assert body["pagination"]["total"] == 2

    def test_filter_by_order_date(self, client, seed_data):
        resp = client.get("/orders?order_date=2024-06-15")
        body = resp.json()
        assert body["pagination"]["total"] == 2

    def test_combined_filters(self, client, seed_data):
        resp = client.get("/orders?status=completed&email=alice@example.com")
        body = resp.json()
        assert body["pagination"]["total"] == 1
        for o in body["data"]:
            assert o["status"] == "completed"
            assert o["customer"]["email"] == "alice@example.com"

    def test_combined_filters_three(self, client, seed_data):
        resp = client.get("/orders?status=completed&email=alice@example.com&order_date=2024-06-15")
        body = resp.json()
        assert body["pagination"]["total"] == 1

    def test_pagination_limit(self, client, seed_data):
        resp = client.get("/orders?limit=1")
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["pagination"]["total"] == 3
        assert body["pagination"]["next_offset"] == 1

    def test_pagination_offset(self, client, seed_data):
        resp = client.get("/orders?limit=1&offset=2")
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["pagination"]["next_offset"] is None

    def test_invalid_limit_over_max(self, client, seed_data):
        resp = client.get("/orders?limit=200")
        assert resp.status_code == 422

    def test_invalid_order_date_format(self, client, seed_data):
        resp = client.get("/orders?order_date=not-a-date")
        assert resp.status_code == 400
        assert "order_date" in resp.json()["detail"]

    def test_invalid_offset_negative(self, client, seed_data):
        resp = client.get("/orders?offset=-1")
        assert resp.status_code == 422

    def test_no_results_filter(self, client, seed_data):
        resp = client.get("/orders?status=shipped")
        body = resp.json()
        assert body["pagination"]["total"] == 0
        assert body["data"] == []
        assert body["pagination"]["next_offset"] is None


class TestCustomersEndpoint:
    def test_get_customers(self, client, seed_data):
        resp = client.get("/customers")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2

    def test_get_customer_by_id(self, client, seed_data):
        resp = client.get("/customers/aaaa1111bbbb2222cccc3333")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Alice Smith"

    def test_customer_not_found(self, client, seed_data):
        resp = client.get("/customers/nonexistent")
        assert resp.status_code == 404
