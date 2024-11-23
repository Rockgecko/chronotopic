"""CSV ingestion utilities."""
import csv
from pathlib import Path
from typing import List

from models import HistoricalEntry
from ingest.base import add_entries, get_db_session
from ingest.markdown_ingest import get_or_create_stories


def ingest_csv(csv_path: Path) -> List[HistoricalEntry]:
    """
    Ingest entries from a CSV file.
    
    Expected columns:
    type,name,begins,ends,location,details,stories
    
    The stories column is optional and can contain comma-separated story names
    """
    entries = []
    session = get_db_session()
    
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Create the entry
            entry = HistoricalEntry(
                type=row['type'],
                name=row['name'],
                begins=row['begins'],
                ends=row['ends'],
                location=row['location'],
                details=row.get('details', '')
            )
            
            # Handle stories if present
            if 'stories' in row and row['stories'].strip():
                story_names = [s.strip() for s in row['stories'].split(',')]
                stories = get_or_create_stories(session, story_names)
                entry.stories.extend(stories)
            
            entries.append(entry)
    
    session.commit()
    return entries


def load_from_csv(csv_path: Path) -> List[HistoricalEntry]:
    """Load entries from CSV file into database."""
    entries = ingest_csv(csv_path)
    if entries:
        add_entries(entries)
    return entries
