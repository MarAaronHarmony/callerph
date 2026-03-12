"""Shared test fixtures."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.db.database import get_engine, reset_engine


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Use an in-memory SQLite database for each test."""
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    reset_engine()

    # Create tables
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup
    SQLModel.metadata.drop_all(engine)
    reset_engine()

    # Remove test db file
    try:
        os.remove("test.db")
    except OSError:
        pass


@pytest.fixture
def session(setup_test_db):
    """Provide a database session for tests."""
    with Session(setup_test_db) as session:
        yield session


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_client(session):
    """Create a sample PagePro client in the database."""
    from app.models.client import Client

    client = Client(
        name="PagePro",
        phone_number="+639171234567",
        prompt_file="pagepro.md",
        is_active=True,
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@pytest.fixture
def sample_call_log(session, sample_client):
    """Create a sample call log entry."""
    from app.models.call_log import CallLog

    call_log = CallLog(
        client_id=sample_client.id,
        twilio_call_sid="CA1234567890abcdef",
        caller_number="+639181234567",
        status="in_progress",
    )
    session.add(call_log)
    session.commit()
    session.refresh(call_log)
    return call_log
