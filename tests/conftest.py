import os
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import database
from app.api import app
from app.models import Customer, Order

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def override_session():
    import app.api as api_module
    import app.database as db_module
    original_api = api_module.SessionLocal
    original_db = db_module.SessionLocal
    api_module.SessionLocal = TestSessionLocal
    db_module.SessionLocal = TestSessionLocal
    yield
    api_module.SessionLocal = original_api
    db_module.SessionLocal = original_db


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_data(db):
    customer = Customer(
        mongo_id="aaaa1111bbbb2222cccc3333",
        name="Alice Smith",
        email="alice@example.com",
        city="New York",
        state="NY",
        country="US",
    )
    customer2 = Customer(
        mongo_id="dddd4444eeee5555ffff6666",
        name="Bob Jones",
        email="bob@example.com",
        city="Los Angeles",
        state="CA",
        country="US",
    )
    db.add_all([customer, customer2])
    db.flush()

    order1 = Order(
        mongo_id="1111aaaa2222bbbb3333cccc",
        customer_mongo_id="aaaa1111bbbb2222cccc3333",
        amount=150.00,
        status="completed",
        source_platform="web_app",
        order_timestamp=datetime(2024, 6, 15, 10, 0, 0),
        purchase_city="New York",
        purchase_state="NY",
        purchase_country="US",
    )
    order2 = Order(
        mongo_id="4444dddd5555eeee6666ffff",
        customer_mongo_id="dddd4444eeee5555ffff6666",
        amount=250.50,
        status="pending",
        source_platform="ios_app",
        order_timestamp=datetime(2024, 7, 20, 14, 30, 0),
        purchase_city="Los Angeles",
        purchase_state="CA",
        purchase_country="US",
    )
    order3 = Order(
        mongo_id="7777aaaa8888bbbb9999cccc",
        customer_mongo_id="aaaa1111bbbb2222cccc3333",
        amount=75.00,
        status="cancelled",
        source_platform="android_app",
        order_timestamp=datetime(2024, 6, 15, 9, 0, 0),
        purchase_city="New York",
        purchase_state="NY",
        purchase_country="US",
    )
    db.add_all([order1, order2, order3])
    db.commit()
    return {"customers": [customer, customer2], "orders": [order1, order2, order3]}


@pytest.fixture
def client():
    return TestClient(app)
