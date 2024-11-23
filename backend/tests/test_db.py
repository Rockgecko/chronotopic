"""Test database models and operations."""
import pytest
from sqlalchemy.exc import IntegrityError

from models.models import Story, HistoricalEntry as Entry

def test_story_creation(test_db):
    """Test creating a story."""
    story = Story(name="Test Story Creation")
    test_db.add(story)
    test_db.commit()

    assert story.id is not None
    assert story.name == "Test Story Creation"

def test_unique_story_name(test_db):
    """Test that story names must be unique."""
    story1 = Story(name="Test Story Unique 1")
    story2 = Story(name="Test Story Unique 1")

    test_db.add(story1)
    test_db.commit()

    test_db.add(story2)
    with pytest.raises(IntegrityError):
        test_db.commit()

@pytest.mark.parametrize("begins,ends,valid", [
    (1900, 1901, True),
    (1901, 1900, False),
    (-500, -400, True),
    (-400, -500, False),
    (-100, 100, True),
])
def test_entry_date_validation(test_db, begins, ends, valid):
    """Test date validation for entries."""
    story = Story(name=f"Test Story Date {begins}-{ends}")
    entry = Entry(
        type="event",
        name=f"Test Event {begins}-{ends}",
        begins=begins,
        ends=ends,
        location="Test Location",
        stories=[story]
    )

    test_db.add(entry)

    if valid:
        test_db.commit()
        assert entry.id is not None
    else:
        with pytest.raises(IntegrityError):
            test_db.commit()

def test_cascade_delete_orphaned_stories(test_db):
    """Test that stories are deleted when no longer referenced."""
    story = Story(name="Test Story Cascade")
    entry = Entry(
        type="event",
        name="Test Event Cascade",
        begins=1900,
        ends=1901,
        location="Test Location",
        stories=[story]
    )

    test_db.add(entry)
    test_db.commit()

    # Delete entry and verify story is also deleted
    test_db.delete(entry)
    test_db.commit()

    # Verify story no longer exists
    story_query = test_db.query(Story).filter_by(name="Test Story Cascade").first()
    assert story_query is None
