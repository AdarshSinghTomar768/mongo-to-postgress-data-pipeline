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