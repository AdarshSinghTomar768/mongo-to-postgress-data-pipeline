import re
from datetime import datetime
from decimal import Decimal

VALID_PLATFORMS = {
    "android_app",
    "ios_app",
    "web_app"
}

VALID_STATUS = {
    "completed",
    "pending",
    "cancelled"
}
EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

def validate_customer(customer):

    required_fields = [
        "_id",
        "name",
        "email",
        "address",
        "signup_date"
    ]

    for field in required_fields:
        if field not in customer or customer[field] in (None, ""):
            return False, f"Missing or empty {field}"

    if not customer["name"].strip():
        return False, "Invalid name"

    if not EMAIL_PATTERN.match(customer["email"]):
        return False, "Invalid email"

    if not isinstance(customer["signup_date"], datetime):
        return False, "Invalid signup_date"

    address = customer["address"]

    for field in ["city", "state", "country"]:
        if field not in address:
            return False, f"Missing address.{field}"

    return True, None


def validate_order(order):

    required_fields = [
        "_id",
        "customer_id",
        "amount",
        "status",
        "source_platform",
        "order_timestamp",
        "purchase_address"
    ]

    for field in required_fields:
        if field not in order or order[field] in (None, ""):
            return False, f"Missing or empty {field}"

    if not isinstance(order["order_timestamp"], datetime):
        return False, "Invalid order_timestamp"

    if not isinstance(order["amount"], Decimal):
        return False, "Invalid amount"

    if order["amount"] <= 0:
        return False, "Amount must be positive"

    if order["source_platform"] not in VALID_PLATFORMS:
        return False, "Invalid source platform"

    if order["status"] not in VALID_STATUS:
        return False, "Invalid status"

    address = order["purchase_address"]

    for field in ["city", "state", "country"]:
        if field not in address:
            return False, f"Missing purchase_address.{field}"

    return True, None