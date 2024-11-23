"""FastAPI application for the chronotopic timeline visualization."""
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.models import Story, HistoricalEntry
from ingest.base import get_db_session
from pydantic import BaseModel, Field, computed_field

app = FastAPI()

class StoryBase(BaseModel):
    """Base model for stories."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class StoryCreate(StoryBase):
    """Model for creating stories."""
    pass

class StoryModel(StoryBase):
    """Model for stories."""
    id: int

class EntryBase(BaseModel):
    """Base model for historical entries."""
    type: str
    name: str
    begins: int
    ends: int
    location: str
    details: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class EntryCreate(EntryBase):
    """Model for creating entries."""
    stories: List[str] = []

class Entry(EntryBase):
    """Model for entries."""
    id: int
    stories: List[str] = []

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/stories", response_model=StoryModel, status_code=status.HTTP_201_CREATED)
def create_story(story: StoryCreate, db: Session = Depends(get_db_session)):
    """Create a new story."""
    try:
        db_story = Story(
            name=story.name,
            description=story.description,
            color=story.color
        )
        db.add(db_story)
        db.commit()
        db.refresh(db_story)
        return db_story
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story with this name already exists"
        )

@app.get("/api/stories", response_model=List[StoryModel])
def get_stories(db: Session = Depends(get_db_session)):
    """Get all stories."""
    return db.query(Story).all()

@app.delete("/api/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: int, db: Session = Depends(get_db_session)):
    """Delete a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    db.delete(story)
    db.commit()
    return None

@app.post("/api/entries", response_model=Entry, status_code=status.HTTP_201_CREATED)
def create_entry(entry: EntryCreate, db: Session = Depends(get_db_session)):
    """Create a new historical entry."""
    try:
        # Create stories if they don't exist
        stories = []
        for story_name in entry.stories:
            story = db.query(Story).filter(Story.name == story_name).first()
            if not story:
                story = Story(name=story_name)
                db.add(story)
            stories.append(story)

        # Create the entry
        db_entry = HistoricalEntry(
            type=entry.type,
            name=entry.name,
            begins=entry.begins,
            ends=entry.ends,
            location=entry.location,
            details=entry.details,
            stories=stories
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        # Convert the stories to a list of names for the response
        return Entry(
            id=db_entry.id,
            type=db_entry.type,
            name=db_entry.name,
            begins=db_entry.begins,
            ends=db_entry.ends,
            location=db_entry.location,
            details=db_entry.details,
            stories=[s.name for s in db_entry.stories]
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entry with this name already exists or date range is invalid"
        )

@app.get("/api/entries", response_model=List[Entry])
def read_entries(
    story: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Read historical entries with optional filtering."""
    query = db.query(HistoricalEntry)
    
    if story:
        query = query.join(HistoricalEntry.stories).filter(Story.name == story)
    if location:
        query = query.filter(HistoricalEntry.location == location)
    
    entries = query.order_by(HistoricalEntry.begins).all()
    
    # Convert the entries to the response model
    return [
        Entry(
            id=entry.id,
            type=entry.type,
            name=entry.name,
            begins=entry.begins,
            ends=entry.ends,
            location=entry.location,
            details=entry.details,
            stories=[s.name for s in entry.stories]
        )
        for entry in entries
    ]

@app.delete("/api/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db_session)):
    """Delete a historical entry."""
    entry = db.query(HistoricalEntry).filter(HistoricalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    db.delete(entry)
    db.commit()
    return None

@app.get("/api/stories/{story_id}/entries", response_model=List[Entry])
def get_entries_by_story(story_id: int, db: Session = Depends(get_db_session)):
    """Get all entries for a specific story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    return [
        Entry(
            id=entry.id,
            type=entry.type,
            name=entry.name,
            begins=entry.begins,
            ends=entry.ends,
            location=entry.location,
            details=entry.details,
            stories=[s.name for s in entry.stories]
        )
        for entry in story.entries
    ]
