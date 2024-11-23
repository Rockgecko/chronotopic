"""Tests for data ingestion functionality."""
import csv
import os
import tempfile
from pathlib import Path
import pytest
from ingest.csv_ingest import parse_story_names, ingest_csv
from ingest.markdown_ingest import ingest_markdown, load_from_markdown
from models import HistoricalEntry, Story

@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['type', 'name', 'begins', 'ends', 'location', 'details', 'stories'])
        writer.writerow(['event', 'Test CSV Event 1', '1900', '1901', 'Test Location', 'Test Details', 'Story A; Story B'])
        writer.writerow(['person', 'Test CSV Person 1', '1800', '1900', 'Test Location', 'Test Details', ''])
    
    yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def sample_markdown_file():
    """Create a temporary markdown file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
type: event
name: Test Markdown Event 1
begins: 1900
ends: 1901
location: Test Location
stories:
  - Test Markdown Story
---
Test Details""")
    
    yield Path(f.name)
    os.unlink(f.name)

def test_parse_story_names():
    """Test parsing story names from CSV cell."""
    # Test empty input
    assert parse_story_names('') == []
    assert parse_story_names(None) == []
    assert parse_story_names('  ') == []
    
    # Test single story
    assert parse_story_names('Story A') == ['Story A']
    
    # Test multiple stories
    assert parse_story_names('Story A; Story B') == ['Story A', 'Story B']
    assert parse_story_names(' Story A;Story B ; Story C ') == ['Story A', 'Story B', 'Story C']

def test_csv_ingestion(test_db, sample_csv_file):
    """Test CSV ingestion functionality."""
    # Test basic ingestion using the test session
    ingest_csv(sample_csv_file, session=test_db)
    
    # Verify entries were created
    entries = test_db.query(HistoricalEntry).all()
    assert len(entries) == 2
    
    # Verify first entry
    event = next(e for e in entries if e.type == 'event')
    assert event.name == 'Test CSV Event 1'
    assert event.begins == 1900
    assert event.ends == 1901
    assert len(event.stories) == 2
    story_names = {s.name for s in event.stories}
    assert story_names == {'Story A', 'Story B'}
    
    # Verify second entry
    person = next(e for e in entries if e.type == 'person')
    assert person.name == 'Test CSV Person 1'
    assert person.begins == 1800
    assert person.ends == 1900
    assert len(person.stories) == 0

def test_csv_error_handling(test_db):
    """Test CSV ingestion error handling."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        ingest_csv(Path('nonexistent.csv'))
    
    # Test malformed CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write('type,name\nincomplete,row\n')
    
    with pytest.raises(KeyError):
        ingest_csv(Path(f.name))
    
    os.unlink(f.name)
    
    # Test invalid dates
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['type', 'name', 'begins', 'ends', 'location', 'details', 'stories'])
        writer.writerow(['event', 'Invalid Date', 'not_a_number', '1901', 'Test Location', '', ''])
    
    with pytest.raises(ValueError):
        ingest_csv(Path(f.name))
    
    os.unlink(f.name)

def test_markdown_ingestion(test_db, sample_markdown_file):
    """Test markdown ingestion functionality."""
    # Test basic ingestion using test session
    ingest_markdown(sample_markdown_file, session=test_db)
    
    # Verify story was created
    story = test_db.query(Story).filter_by(name='Test Markdown Story').first()
    assert story is not None
    
    # Verify entry was created and linked to story
    entry = test_db.query(HistoricalEntry).filter_by(name='Test Markdown Event 1').first()
    assert entry is not None
    assert entry.name == 'Test Markdown Event 1'
    assert entry.type == 'event'
    assert entry.begins == 1900
    assert entry.ends == 1901
    assert len(entry.stories) == 1
    assert entry.stories[0].name == 'Test Markdown Story'

def test_markdown_error_handling(test_db):
    """Test markdown ingestion error handling."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        ingest_markdown(Path('nonexistent.md'), session=test_db)
    
    # Test malformed markdown
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
invalid: frontmatter
---
Invalid content
""")
    
    with pytest.raises(KeyError):
        ingest_markdown(f.name, session=test_db)
    
    os.unlink(f.name)
    
    # Test missing required fields
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
type: event
name: Incomplete Event
---""")
    
    with pytest.raises(KeyError):
        ingest_markdown(f.name, session=test_db)
    
    os.unlink(f.name)
