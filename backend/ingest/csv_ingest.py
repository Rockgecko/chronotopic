"""CSV ingestion utilities."""
import csv
from pathlib import Path
from typing import List

from models import HistoricalEntry
from ingest.base import get_db_session
from ingest.markdown_ingest import get_or_create_stories


def parse_story_names(stories_str: str) -> List[str]:
    """Parse story names from CSV cell."""
    if not stories_str or stories_str.strip() == '':
        return []
    
    # Split by semicolon and strip whitespace
    return [s.strip() for s in stories_str.split(';') if s.strip()]


def ingest_csv(csv_path: Path, db_path: str = "history.db", session=None) -> None:
    """
    Ingest entries from a CSV file.
    
    Expected CSV columns:
    - type: event/person
    - name: Name of the entry
    - begins: Year (negative for BCE)
    - ends: Year (negative for BCE)
    - location: Location of the entry
    - details: Optional detailed description
    - stories: Optional semicolon-separated list of story names e.g., "Story1; Story2"
    """
    if session is None:
        session = get_db_session(db_path)
        close_session = True
    else:
        close_session = False

    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Parse stories if present
                story_names = parse_story_names(row.get('stories', ''))
                stories = get_or_create_stories(session, story_names) if story_names else []
                
                # Create entry
                entry = HistoricalEntry(
                    type=row['type'],
                    name=row['name'],
                    begins=int(row['begins']),
                    ends=int(row['ends']),
                    location=row['location'],
                    details=row.get('details', ''),
                    stories=stories
                )
                session.add(entry)
        
        session.commit()
    finally:
        if close_session:
            session.close()


def load_from_csv(csv_path: str, db_path: str) -> None:
    """Load entries from a CSV file into the database."""
    ingest_csv(Path(csv_path), db_path)
