"""Tests for client lookup by phone number."""

from sqlmodel import select

from app.models.client import Client


def test_create_client(session):
    client = Client(
        name="Test Business",
        phone_number="+639990001111",
        prompt_file="test.md",
        is_active=True,
    )
    session.add(client)
    session.commit()
    session.refresh(client)

    assert client.id is not None
    assert client.name == "Test Business"


def test_lookup_by_phone_number(session, sample_client):
    result = session.exec(
        select(Client).where(Client.phone_number == "+639171234567")
    ).first()

    assert result is not None
    assert result.name == "PagePro"


def test_lookup_unknown_number(session, sample_client):
    result = session.exec(
        select(Client).where(Client.phone_number == "+639999999999")
    ).first()

    assert result is None


def test_lookup_inactive_client(session):
    client = Client(
        name="Inactive Business",
        phone_number="+639330001111",
        prompt_file="inactive.md",
        is_active=False,
    )
    session.add(client)
    session.commit()

    result = session.exec(
        select(Client).where(
            Client.phone_number == "+639330001111",
            Client.is_active == True,  # noqa: E712
        )
    ).first()

    assert result is None
