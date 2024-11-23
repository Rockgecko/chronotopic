"""Tests for the chronotopic API endpoints."""
import pytest
from fastapi import status
from models import HistoricalEntry, Story

# Core fixtures
@pytest.fixture
def sample_story():
    """Basic story fixture."""
    return {
        "name": "Test Story",
        "description": "Test Description",
        "color": "#FF0000"
    }

@pytest.fixture
def sample_entry():
    """Basic entry fixture."""
    return {
        "type": "event",
        "name": "Test Event",
        "begins": 1900,
        "ends": 1901,
        "location": "Test Location",
        "details": "Test Details",
        "stories": ["Test Story"]
    }

# Story Tests
def test_story_lifecycle(client, test_db, sample_story):
    """Test complete story lifecycle: create, read, update, delete."""
    # Create
    response = client.post("/api/stories", json=sample_story)
    assert response.status_code == status.HTTP_201_CREATED
    story_id = response.json()["id"]
    
    # Read
    response = client.get("/api/stories")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == sample_story["name"]
    
    # Delete
    response = client.delete(f"/api/stories/{story_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

# Entry Tests
def test_entry_lifecycle(client, test_db, sample_entry, sample_story):
    """Test complete entry lifecycle with story association."""
    # Create prerequisite story
    client.post("/api/stories", json=sample_story)
    
    # Create entry
    response = client.post("/api/entries", json=sample_entry)
    assert response.status_code == status.HTTP_201_CREATED
    entry_id = response.json()["id"]
    
    # Read and verify
    response = client.get("/api/entries")
    assert response.status_code == status.HTTP_200_OK
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["name"] == sample_entry["name"]
    assert "Test Story" in entries[0]["stories"]
    
    # Delete
    response = client.delete(f"/api/entries/{entry_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_entry_validation(client, test_db, sample_entry):
    """Test entry validation rules."""
    # Test invalid date range
    invalid_entry = sample_entry.copy()
    invalid_entry["begins"] = 1901
    invalid_entry["ends"] = 1900
    response = client.post("/api/entries", json=invalid_entry)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test missing required field
    invalid_entry = sample_entry.copy()
    del invalid_entry["name"]
    response = client.post("/api/entries", json=invalid_entry)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Filtering Tests
def test_entry_filtering(client, test_db):
    """Test entry filtering by story and location."""
    # Create test data
    stories = [
        {"name": "Story A", "description": "Test"},
        {"name": "Story B", "description": "Test"}
    ]
    for story in stories:
        client.post("/api/stories", json=story)
    
    entries = [
        {
            "type": "event",
            "name": "Event 1",
            "begins": 1800,
            "ends": 1850,
            "location": "Location A",
            "details": "Details",
            "stories": ["Story A"]
        },
        {
            "type": "event",
            "name": "Event 2",
            "begins": 1820,
            "ends": 1840,
            "location": "Location B",
            "details": "Details",
            "stories": ["Story A", "Story B"]
        }
    ]
    
    for entry in entries:
        client.post("/api/entries", json=entry)
    
    # Test story filter
    response = client.get("/api/entries?story=Story A")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    
    response = client.get("/api/entries?story=Story B")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    
    # Test location filter
    response = client.get("/api/entries?location=Location A")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

# Error Handling Tests
def test_error_handling(client, test_db, sample_entry):
    """Test API error handling."""
    # Test non-existent entry
    response = client.delete("/api/entries/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Test duplicate entry name
    client.post("/api/entries", json=sample_entry)
    response = client.post("/api/entries", json=sample_entry)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
