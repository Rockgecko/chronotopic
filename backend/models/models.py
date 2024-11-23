from sqlalchemy import Column, Integer, String, ForeignKey, Table, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# Junction table for story-entry relationships
story_entries = Table(
    'story_entries',
    Base.metadata,
    Column('story_id', Integer, ForeignKey('stories.id'), primary_key=True),
    Column('entry_id', Integer, ForeignKey('historical_entries.id'), primary_key=True)
)

class Story(Base):
    __tablename__ = 'stories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    color = Column(String, nullable=True)
    
    entries = relationship('HistoricalEntry', secondary=story_entries, back_populates='stories')

class HistoricalEntry(Base):
    __tablename__ = 'historical_entries'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    name = Column(String)
    begins = Column(Integer)  # Negative for BCE, Positive for CE
    ends = Column(Integer)    # Negative for BCE, Positive for CE
    location = Column(String)
    details = Column(String)
    
    stories = relationship('Story', secondary=story_entries, back_populates='entries')

    # Ensure ends is not before begins
    __table_args__ = (
        CheckConstraint('ends >= begins', name='valid_date_range'),
    )
