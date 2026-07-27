from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Customer, Order

app = FastAPI(title="Mongo to PostgreSQL Data Pipeline API")


class CustomerResponse(BaseModel):
    mongo_id: str | None = None
    name: str | None = None
    email: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    signup_date: datetime | None = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    mongo_id: str | None = None
    customer_mongo_id: str | None = None
    amount: float | None = None
    status: str | None = None
    source_platform: str | None = None
    order_timestamp: datetime | None = None
    purchase_city: str | None = None
    purchase_state: str | None = None
    purchase_country: str | None = None
    customer: CustomerResponse | None = None

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int
    next_offset: int | None = None


class PaginatedOrdersResponse(BaseModel):
    data: list[OrderResponse]
    pagination: PaginationMeta


@app.get("/orders")
def get_orders(
    order_date: str | None = None,
    customer_id: str | None = None,
    email: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db: Session = SessionLocal()

    try:
        query = db.query(Order).join(Customer, Order.customer_mongo_id == Customer.mongo_id)

        if order_date is not None:
            try:
                parsed_date = date.fromisoformat(order_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid order_date format. Use YYYY-MM-DD.",
                )
            start = datetime.combine(parsed_date, datetime.min.time())
            end = datetime.combine(parsed_date, datetime.max.time())
            query = query.filter(
                Order.order_timestamp >= start,
                Order.order_timestamp <= end,
            )

        if customer_id is not None:
            query = query.filter(Order.customer_mongo_id == customer_id)

        if email is not None:
            query = query.filter(func.lower(Customer.email) == email.lower())

        if status is not None:
            query = query.filter(Order.status == status)

        total = query.count()

        orders = (
            query
            .order_by(Order.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        next_offset = offset + limit if offset + limit < total else None

        return PaginatedOrdersResponse(
            data=[
                OrderResponse(
                    mongo_id=o.mongo_id,
                    customer_mongo_id=o.customer_mongo_id,
                    amount=float(o.amount) if o.amount else None,
                    status=o.status,
                    source_platform=o.source_platform,
                    order_timestamp=o.order_timestamp,
                    purchase_city=o.purchase_city,
                    purchase_state=o.purchase_state,
                    purchase_country=o.purchase_country,
                    customer=CustomerResponse(
                        mongo_id=o.customer.mongo_id,
                        name=o.customer.name,
                        email=o.customer.email,
                        city=o.customer.city,
                        state=o.customer.state,
                        country=o.customer.country,
                        signup_date=o.customer.signup_date,
                    ) if o.customer else None,
                )
                for o in orders
            ],
            pagination=PaginationMeta(
                total=total,
                limit=limit,
                offset=offset,
                next_offset=next_offset,
            ),
        )

    finally:
        db.close()


@app.get("/customers")
def get_customers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db: Session = SessionLocal()

    try:
        total = db.query(func.count(Customer.id)).scalar()

        customers = (
            db.query(Customer)
            .order_by(Customer.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return customers

    finally:
        db.close()


@app.get("/customers/{mongo_id}")
def get_customer(mongo_id: str):
    db: Session = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.mongo_id == mongo_id)
            .first()
        )

        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        return customer

    finally:
        db.close()


@app.get("/orders/{mongo_id}")
def get_order(mongo_id: str):
    db: Session = SessionLocal()

    try:
        order = (
            db.query(Order)
            .filter(Order.mongo_id == mongo_id)
            .first()
        )

        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        return order

    finally:
        db.close()
