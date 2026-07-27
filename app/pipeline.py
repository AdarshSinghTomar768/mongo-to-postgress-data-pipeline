from sqlalchemy.exc import IntegrityError

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
    """

    rejected = RejectedRecord(
        source_type=source_type,
        source_id=source_id,
        rejection_reason=reason,
        raw_record=raw_record,
    )

    try:
        session.add(rejected)
        session.flush()

    except IntegrityError:
        session.rollback()


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

    for customer in load_jsonl("data/customers.jsonl"):

        # Validate customer
        valid, reason = validate_customer(customer)

        if not valid:
            reject_record(
                session=session,
                source_type="customer",
                source_id=customer.get("_id"),
                reason=reason,
                raw_record=customer,
            )
            continue

        # Check duplicate customer
        if customer_exists(session, customer["_id"]):
            reject_record(
                session=session,
                source_type="customer",
                source_id=customer["_id"],
                reason="Duplicate customer",
                raw_record=customer,
            )
            continue

        # Create Customer ORM object
        new_customer = Customer(
            mongo_id=customer["_id"],
            name=customer["name"],
            email=customer["email"],
            city=customer["address"]["city"],
            state=customer["address"]["state"],
            country=customer["address"]["country"],
            signup_date=customer["signup_date"],
        )

        session.add(new_customer)

    try:
        session.commit()
        print("Customers loaded successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error while loading customers: {e}")



def load_orders(session):
    """
    Read orders.jsonl and insert valid orders.
    """

    print("Loading orders...")

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

        # Check duplicate order
        if order_exists(session, order["_id"]):
            reject_record(
                session=session,
                source_type="order",
                source_id=order["_id"],
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
                source_id=order["_id"],
                reason="Customer does not exist",
                raw_record=order,
            )
            continue

        # Create Order ORM object
        new_order = Order(
            mongo_id=order["_id"],
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

    except Exception as e:
        session.rollback()
        print(f"Pipeline failed: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    main()