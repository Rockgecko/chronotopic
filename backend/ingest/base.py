"""Base utilities for data ingestion."""

from typing import List

from models import Base, HistoricalEntry
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_db_session(db_path: str = "history.db") -> Session:
    """Create a database session."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
