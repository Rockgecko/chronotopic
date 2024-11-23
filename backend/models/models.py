"""Database models for the chronotopic application."""
from sqlalchemy import Column, Integer, String, Table, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import relationship, Session

from models.base import Base

story_entries = Table(
    "story_entries",
    Base.metadata,
    Column("story_id", Integer, ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
    Column("entry_id", Integer, ForeignKey("historical_entries.id", ondelete="CASCADE"), primary_key=True),
)

class Story(Base):
    """Model for stories."""
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    color = Column(String)

    entries = relationship(
        "HistoricalEntry",
        secondary=story_entries,
        back_populates="stories",
        passive_deletes=True,
    )

class HistoricalEntry(Base):
    """Model for historical entries."""
    __tablename__ = "historical_entries"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    name = Column(String, unique=True, nullable=False)
    begins = Column(Integer, nullable=False)
    ends = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    details = Column(String)

    stories = relationship(
        "Story",
        secondary=story_entries,
        back_populates="entries",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("ends >= begins", name="valid_date_range"),
    )

@event.listens_for(HistoricalEntry, "after_delete")
def delete_orphaned_stories(mapper, connection, target):
    """Delete stories that are no longer referenced by any entries."""
    # Get the session from the connection
    session = Session.object_session(target)
    if session is None:
        return

    # Find and delete orphaned stories
    for story in target.stories:
        if len(story.entries) <= 1:  # Will be 1 because the entry isn't fully deleted yet
            session.delete(story)
