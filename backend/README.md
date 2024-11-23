# Chronotopic Backend

A FastAPI-based backend for the Chronotopic historical timeline visualization project. Handles data ingestion, storage, and API endpoints for historical events and stories.

## Setup

The project uses Python 3.11 and `uv` for dependency management. Dependencies are defined in `pyproject.toml`.

```bash
# Create a new virtual environment and install dependencies
cd backend
uv sync
```

## Database Management

The system uses SQLite for data storage (`history.db`). The database schema supports:

- Historical entries (events/people) with BCE/CE dates
- Stories (collections of related entries)
- Many-to-many relationships between entries and stories

### Command Line Interface

All commands should be run from the `backend` directory:

```bash
# List all entries
uv run --python=3.11 python3 -m manage_db list-entries

# List all stories
uv run --python=3.11 python3 -m manage_db list-stories

# Show details of a specific story
uv run --python=3.11 python3 -m manage_db show-story 1

# Create a new story
uv run --python=3.11 python3 -m manage_db create-story "Industrial Revolution" --description "Major technological changes" --color "#FF0000"

# Add entries to a story
uv run --python=3.11 python3 -m manage_db add-to-story 1 2 3 4

# Remove entries from a story
uv run --python=3.11 python3 -m manage_db remove-from-story 1 2 3
```

### Data Ingestion

The system supports both Markdown and CSV ingestion.

#### Markdown Format

```markdown
---
type: event
name: Event Name
begins: 1769        # Use negative numbers for BCE (e.g., -500 for 500 BCE)
ends: 1769
location: Location
stories: ["Story1", "Story2"]  # Optional
---

Detailed description of the event...
```

To ingest markdown files:

```bash
uv run --python=3.11 python3 -m manage_db load-md examples/steam_power.md
```

#### CSV Format

Coming soon...

## Running the Server

Start the FastAPI server from the `backend` directory:

```bash
uv run --python=3.11 python3 -m uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

### API Endpoints

- `GET /api/entries` - Get all historical entries with their stories
- `GET /api/stories` - Get all stories
- `GET /api/stories/{story_id}/entries` - Get entries for a specific story

## Development Notes

### Date Handling

- Years are stored as integers
- BCE years are negative (e.g., -500 for 500 BCE)
- CE years are positive (e.g., 1769 for 1769 CE)
- The database enforces that end dates cannot be before start dates

### Project Structure

backend/
├── models/         # SQLAlchemy models
├── ingest/        # Data ingestion utilities
├── examples/      # Example data files
├── main.py        # FastAPI application
├── manage_db.py   # CLI tools
└── pyproject.toml # Project dependencies and metadata
