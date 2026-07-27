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
        session.commit()

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