from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///history.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define database model
class HistoricalEntry(Base):
    __tablename__ = "historical_entries"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    name = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    location = Column(String)
    details = Column(String)


Base.metadata.create_all(bind=engine)


def add_initial_data():
    db = SessionLocal()
    if db.query(HistoricalEntry).count() == 0:
        entries = [
            HistoricalEntry(
                type="event",
                name="Event A",
                start_date=date(1800, 1, 1),
                end_date=date(1820, 1, 1),
                location="Europe",
                details="Details about Event A",
            ),
            HistoricalEntry(
                type="event",
                name="Event B",
                start_date=date(1850, 1, 1),
                end_date=date(1860, 1, 1),
                location="America",
                details="Details about Event B",
            ),
            HistoricalEntry(
                type="person",
                name="Person X",
                start_date=date(1880, 1, 1),
                end_date=date(1930, 1, 1),
                location="Asia",
                details="Biography of Person X",
            ),
        ]
        db.add_all(entries)
        db.commit()
    db.close()


# Call the function to add initial data
add_initial_data()

# FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # You can replace "*" with specific domains for better security.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for response
class HistoricalEntryResponse(BaseModel):
    id: int
    type: str
    name: str
    start_date: str
    end_date: str
    location: str
    details: str

    class Config:
        orm_mode = True


@app.get("/entries/", response_model=list[HistoricalEntryResponse])
def get_entries():
    db = SessionLocal()
    entries = db.query(HistoricalEntry).all()
    db.close()

    # Convert start_date and end_date to string
    result = [
        {
            "id": entry.id,
            "type": entry.type,
            "name": entry.name,
            "start_date": entry.start_date.strftime("%Y-%m-%d")
            if entry.start_date
            else None,
            "end_date": entry.end_date.strftime("%Y-%m-%d") if entry.end_date else None,
            "location": entry.location,
            "details": entry.details,
        }
        for entry in entries
    ]

    return result
