"""Markdown ingestion utilities."""
from pathlib import Path
from typing import List, Optional

import frontmatter
from models import HistoricalEntry, Story
from ingest.base import add_entries, get_db_session


def get_or_create_stories(session, story_names: List[str]) -> List[Story]:
    """Get existing stories or create new ones."""
    stories = []
    for name in story_names:
        story = session.query(Story).filter_by(name=name).first()
        if not story:
            story = Story(name=name)
            session.add(story)
            session.flush()  # Ensure the story has an ID before using it in relationships
        stories.append(story)
    return stories


def ingest_markdown(md_path: Path, session=None) -> HistoricalEntry:
    """
    Ingest entries from a markdown file.
    
    The markdown file should have frontmatter with the following fields:
    - type: The type of entry (e.g., "event", "person")
    - name: The name of the entry
    - begins: The year when the entry begins (negative for BCE)
    - ends: The year when the entry ends (negative for BCE)
    - location: The location of the entry
    - stories: (optional) List of story names this entry belongs to
    
    The content of the markdown file will be used as the entry's details.
    """
    if session is None:
        session = get_db_session()
        close_session = True
    else:
        close_session = False
    
    try:
        with open(md_path) as f:
            post = frontmatter.load(f)
        
        # Create stories if they don't exist
        story_names = post.get('stories', [])
        stories = get_or_create_stories(session, story_names)
        
        # Create the entry
        entry = HistoricalEntry(
            type=post['type'],
            name=post['name'],
            begins=post['begins'],
            ends=post['ends'],
            location=post['location'],
            details=post.content.strip(),
            stories=stories
        )
        
        # Add and commit
        session.add(entry)
        session.commit()
        
        return entry
    finally:
        if close_session:
            session.close()


def ingest_markdown_directory(directory: Path, session=None) -> List[HistoricalEntry]:
    """Ingest all markdown files in a directory."""
    entries = []
    for md_file in directory.glob("*.md"):
        entry = ingest_markdown(md_file, session=session)
        if entry:
            entries.append(entry)
    return entries


def load_from_markdown(md_path: str, db_path: str) -> None:
    """Load entries from a markdown file into the database."""
    session = get_db_session(db_path)
    try:
        entry = ingest_markdown(Path(md_path), session=session)
    finally:
        session.close()
