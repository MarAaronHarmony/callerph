"""Seed database with initial client data."""

from sqlmodel import Session, select

from app.db.database import create_db_and_tables, get_engine
from app.models.client import Client


def seed_pagepro(phone_number: str = "+639000000000"):
    """Create PagePro client record if it doesn't exist."""
    create_db_and_tables()
    engine = get_engine()

    with Session(engine) as session:
        existing = session.exec(
            select(Client).where(Client.name == "PagePro")
        ).first()

        if existing:
            print(f"PagePro client already exists (id={existing.id})")
            return existing

        client = Client(
            name="PagePro",
            phone_number=phone_number,
            prompt_file="pagepro.md",
            is_active=True,
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        print(f"PagePro client created (id={client.id}, phone={phone_number})")
        return client


if __name__ == "__main__":
    import sys

    phone = sys.argv[1] if len(sys.argv) > 1 else "+639000000000"
    seed_pagepro(phone)
