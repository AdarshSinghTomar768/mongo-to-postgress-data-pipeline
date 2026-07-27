import json
from decimal import Decimal
from datetime import datetime
from decimal import Decimal, InvalidOperation

def parse_extended_json(value):
    """
    Recursively converts MongoDB Extended JSON
    into normal Python objects.
    """

    if isinstance(value, dict):

        if "$oid" in value:
            return value["$oid"]

        if "$date" in value:
            try:
                return datetime.fromisoformat(
                    value["$date"].replace("Z", "+00:00")
                )
            except ValueError:
                return value["$date"]

        if "$numberDecimal" in value:
            try:
                return Decimal(value["$numberDecimal"])
            except (InvalidOperation, TypeError):
                return value["$numberDecimal"]

        return {
            key: parse_extended_json(val)
            for key, val in value.items()
        }

    elif isinstance(value, list):
        return [
            parse_extended_json(item)
            for item in value
        ]

    return value


def load_jsonl(file_path):
    """
    Reads a JSONL file line by line
    and returns parsed records.
    """

    with open(file_path, "r") as file:
        for line in file:
            record = json.loads(line)
            yield parse_extended_json(record)