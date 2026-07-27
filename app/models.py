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