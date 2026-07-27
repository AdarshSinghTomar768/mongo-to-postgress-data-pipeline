from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    ForeignKey,
    JSON,
)

from sqlalchemy.orm import relationship

from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    mongo_id = Column(String(24), unique=True, nullable=False)

    name = Column(String, nullable=False)

    email = Column(String, nullable=False)

    city = Column(String)

    state = Column(String)

    country = Column(String)

    signup_date = Column(DateTime)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    mongo_id = Column(String(24), unique=True, nullable=False)

    customer_mongo_id = Column(
        String(24),
        ForeignKey("customers.mongo_id"),
        nullable=False
    )

    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(String, nullable=False)

    source_platform = Column(String, nullable=False)

    order_timestamp = Column(DateTime, nullable=False)

    purchase_city = Column(String)

    purchase_state = Column(String)

    purchase_country = Column(String)

    customer = relationship(
        "Customer",
        back_populates="orders"
    )


class RejectedRecord(Base):
    __tablename__ = "rejected_records"

    id = Column(Integer, primary_key=True, index=True)

    source_type = Column(String, nullable=False)

    source_id = Column(String)

    rejection_reason = Column(String, nullable=False)

    raw_record = Column(JSON, nullable=False)