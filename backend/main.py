from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ingest.base import get_db_session
from models import HistoricalEntry, Story

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

class EntryBase(BaseModel):
    type: str
    name: str
    begins: int = Field(
        description="Year when the event/person begins. Use negative numbers for BCE (e.g., -500 for 500 BCE) and positive for CE"
    )
    ends: int = Field(
        description="Year when the event/person ends. Use negative numbers for BCE (e.g., -500 for 500 BCE) and positive for CE"
    )
    location: str
    details: Optional[str] = None
    stories: List[StoryBase] = []

    class Config:
        from_attributes = True

    @property
    def begins_formatted(self) -> str:
        """Format begins year as BCE/CE string."""
        return f"{abs(self.begins)} {'BCE' if self.begins < 0 else 'CE'}"

    @property
    def ends_formatted(self) -> str:
        """Format ends year as BCE/CE string."""
        return f"{abs(self.ends)} {'BCE' if self.ends < 0 else 'CE'}"

@app.get("/api/entries", response_model=List[EntryBase])
def get_entries():
    """Get all historical entries with their associated stories."""
    session = get_db_session()
    entries = session.query(HistoricalEntry).all()
    return entries

@app.get("/api/stories", response_model=List[StoryBase])
def get_stories():
    """Get all stories."""
    session = get_db_session()
    stories = session.query(Story).all()
    return stories

@app.get("/api/stories/{story_id}/entries", response_model=List[EntryBase])
def get_story_entries(story_id: int):
    """Get all entries for a specific story."""
    session = get_db_session()
    story = session.query(Story).filter_by(id=story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story.entries
