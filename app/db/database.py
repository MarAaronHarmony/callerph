from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def create_db_and_tables():
    import app.models.client  # noqa: F401
    import app.models.call_log  # noqa: F401

    SQLModel.metadata.create_all(get_engine())


def get_session():
    with Session(get_engine()) as session:
        yield session


def reset_engine():
    """Reset engine — used in tests to switch databases."""
    global _engine
    _engine = None
