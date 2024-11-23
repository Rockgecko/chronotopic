"""Base utilities for data ingestion."""

from typing import List

from models.base import Base
from models.models import HistoricalEntry  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_db_engine(db_path: str = "history.db"):
    """Create a database engine."""
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )


_engine = create_db_engine()
Base.metadata.create_all(bind=_engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db_session(db_path: str = "history.db") -> SessionLocal:
    """Get a database session."""
    global _engine, SessionLocal
    
    # If db_path is different from current engine, create new engine
    if f"sqlite:///{db_path}" != str(_engine.url):
        _engine = create_db_engine(db_path)
        Base.metadata.create_all(bind=_engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    return SessionLocal()


def add_entries(entries: List[HistoricalEntry], db_path: str = "history.db") -> None:
    """Add multiple entries to the database."""
    db = get_db_session(db_path)
    try:
        db.add_all(entries)
        db.commit()
    finally:
        db.close()


def clear_database(db_path: str = "history.db") -> None:
    """Clear all entries from the database."""
    db = get_db_session(db_path)
    try:
        db.query(HistoricalEntry).delete()
        db.commit()
    finally:
        db.close()
