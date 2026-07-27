from sqlalchemy.exc import IntegrityError
import json
import traceback

from app.database import SessionLocal, Base, engine
from app.models import Customer, Order, RejectedRecord
from app.parser import load_jsonl
from app.validator import validate_customer, validate_order


# Create tables if they don't already exist
Base.metadata.create_all(bind=engine)


def reject_record(session, source_type, source_id, reason, raw_record):
    """
    Stores rejected records.
    If the same rejected record already exists,
    ignore it to keep the pipeline idempotent.
    Uses a savepoint so that a duplicate rejection
    does not roll back other pending inserts.
    """

    rejected = RejectedRecord(
        source_type=source_type,
        source_id=source_id,
        rejection_reason=reason,
        raw_record=json.loads(
            json.dumps(
                raw_record,
                default=str
            )
        ),
    )

    savepoint = session.begin_nested()
    try:
        session.add(rejected)
        session.flush()
        savepoint.commit()
    except IntegrityError:
        savepoint.rollback()


def customer_exists(session, mongo_id):
    """
    Returns True if customer already exists.
    """

    return (
        session.query(Customer)
        .filter(Customer.mongo_id == mongo_id)
        .first()
        is not None
    )


def order_exists(session, mongo_id):
    """
    Returns True if order already exists.
    """

    return (
        session.query(Order)
        .filter(Order.mongo_id == mongo_id)
        .first()
        is not None
    )



def load_customers(session):
    """
    Read customers.jsonl and insert valid customers.
    """

    print("Loading customers...")

    count = 0
    valid_count = 0
    rejected_count = 0
    seen_ids = set()

    for customer in load_jsonl("data/customers.jsonl"):
        count += 1

        valid, reason = validate_customer(customer)

        if not valid:
            rejected_count += 1

            if rejected_count <= 10:
                print(f"Rejected: {customer.get('_id')} -> {reason}")

            reject_record(
                session=session,
                source_type="customer",
                source_id=customer.get("_id"),
                reason=reason,
                raw_record=customer,
            )
            continue

        valid_count += 1

        if valid_count <= 10:
            print(f"Valid: {customer['_id']}")

        mongo_id = customer["_id"]

        if mongo_id in seen_ids or customer_exists(session, mongo_id):
            reject_record(
                session=session,
                source_type="customer",
                source_id=mongo_id,
                reason="Duplicate customer",
                raw_record=customer,
            )
            continue

        seen_ids.add(mongo_id)
        session.add(
            Customer(
                mongo_id=mongo_id,
                name=customer["name"],
                email=customer["email"],
                city=customer["address"]["city"],
                state=customer["address"]["state"],
                country=customer["address"]["country"],
                signup_date=customer["signup_date"],
            )
        )

    print(f"Read: {count}")
    print(f"Valid: {valid_count}")
    print(f"Rejected: {rejected_count}")
    print(f"Pending inserts: {len(session.new)}")

    session.commit()



def load_orders(session):
    """
    Read orders.jsonl and insert valid orders.
    """

    print("Loading orders...")

    seen_ids = set()

    for order in load_jsonl("data/orders.jsonl"):

        # Validate order
        valid, reason = validate_order(order)

        if not valid:
            reject_record(
                session=session,
                source_type="order",
                source_id=order.get("_id"),
                reason=reason,
                raw_record=order,
            )
            continue

        mongo_id = order["_id"]

        # Check duplicate order
        if mongo_id in seen_ids or order_exists(session, mongo_id):
            reject_record(
                session=session,
                source_type="order",
                source_id=mongo_id,
                reason="Duplicate order",
                raw_record=order,
            )
            continue

        # Check whether customer exists
        customer = (
            session.query(Customer)
            .filter(Customer.mongo_id == order["customer_id"])
            .first()
        )

        if customer is None:
            reject_record(
                session=session,
                source_type="order",
                source_id=mongo_id,
                reason="Customer does not exist",
                raw_record=order,
            )
            continue

        seen_ids.add(mongo_id)

        # Create Order ORM object
        new_order = Order(
            mongo_id=mongo_id,
            customer_mongo_id=order["customer_id"],
            amount=order["amount"],
            status=order["status"],
            source_platform=order["source_platform"],
            order_timestamp=order["order_timestamp"],
            purchase_city=order["purchase_address"]["city"],
            purchase_state=order["purchase_address"]["state"],
            purchase_country=order["purchase_address"]["country"],
        )

        session.add(new_order)

    try:
        session.commit()
        print("Orders loaded successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error while loading orders: {e}")



def main():
    """
    Main ETL pipeline execution.
    """

    session = SessionLocal()

    try:
        print("=" * 50)
        print("Starting ETL Pipeline")
        print("=" * 50)

        # Load customers first
        load_customers(session)

        # Then load orders
        load_orders(session)

        print("=" * 50)
        print("ETL Pipeline Completed Successfully")
        print("=" * 50)

    except Exception:
        session.rollback()
        traceback.print_exc()

    finally:
        session.close()


if __name__ == "__main__":
    main()