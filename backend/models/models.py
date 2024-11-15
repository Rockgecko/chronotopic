from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class HistoricalEntry(Base):
    __tablename__ = 'historical_entries'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    name = Column(String)
    begins = Column(Date)
    ends = Column(Date)
    location = Column(String)
    details = Column(String)
