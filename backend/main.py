from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.models import Base, HistoricalEntry

engine = create_engine("sqlite:///history.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def add_initial_data():
    db = SessionLocal()
    if db.query(HistoricalEntry).count() == 0:
        entries = [
            HistoricalEntry(
                type="event",
                name="Event A",
                begins=date(1800, 1, 1),
                ends=date(1820, 1, 1),
                location="Europe",
                details="Details about Event A",
            ),
            HistoricalEntry(
                type="event",
                name="Event B",
                begins=date(1850, 1, 1),
                ends=date(1860, 1, 1),
                location="America",
                details="Details about Event B",
            ),
            HistoricalEntry(
                type="person",
                name="Person X",
                begins=date(1880, 1, 1),
                ends=date(1930, 1, 1),
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HistoricalEntryResponse(BaseModel):
    id: int
    type: str
    name: str
    begins: str
    ends: str
    location: str
    details: str

    class Config:
        orm_mode = True


@app.get("/entries/", response_model=list[HistoricalEntryResponse])
def get_entries():
    db = SessionLocal()
    entries = db.query(HistoricalEntry).all()
    db.close()

    return [
        {
            "id": entry.id,
            "type": entry.type,
            "name": entry.name,
            "begins": (
                entry.begins.strftime("%Y-%m-%d")
                if entry.begins
                else None
            ),
            "ends": (
                entry.ends.strftime("%Y-%m-%d") if entry.ends else None
            ),
            "location": entry.location,
            "details": entry.details,
        }
        for entry in entries
    ]
