#!/usr/bin/env python3
"""Database management script."""
from pathlib import Path
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ingest.base import clear_database
from ingest.csv_ingest import load_from_csv
from ingest.markdown_ingest import load_from_markdown
from models import HistoricalEntry, Base, Story

app = typer.Typer(help="Manage historical timeline database", pretty_exceptions_enable=False)
console = Console()

def get_db_session(db_path: str = "history.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
    Session = sessionmaker(bind=engine)
    return Session()

@app.command()
def clear(
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    )
):
    """Clear all entries from the database."""
    clear_database(str(db_path))
    print("[green]Database cleared successfully[/green]")

@app.command()
def load_csv(
    csv_path: Path = typer.Argument(
        ...,
        help="Path to CSV file",
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """Load entries from a CSV file."""
    load_from_csv(csv_path, str(db_path))
    print(f"[green]Successfully loaded entries from[/green] {csv_path}")

@app.command()
def load_md(
    md_path: Path = typer.Argument(
        ...,
        help="Path to markdown file or directory",
        exists=True,
        readable=True,
    ),
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """Load entries from markdown file(s)."""
    load_from_markdown(md_path, str(db_path))
    if md_path.is_file():
        print(f"[green]Successfully loaded entry from[/green] {md_path}")
    else:
        print(f"[green]Successfully loaded entries from directory[/green] {md_path}")

@app.command()
def info(
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """Show database information."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
    Session = sessionmaker(bind=engine)
    session = Session()

    total_entries = session.query(func.count(HistoricalEntry.id)).scalar()
    events = session.query(func.count(HistoricalEntry.id)).filter(HistoricalEntry.type == "event").scalar()
    people = session.query(func.count(HistoricalEntry.id)).filter(HistoricalEntry.type == "person").scalar()
    locations = session.query(func.count(func.distinct(HistoricalEntry.location))).scalar()

    earliest = session.query(func.min(HistoricalEntry.begins)).scalar()
    latest = session.query(func.max(HistoricalEntry.ends)).scalar()

    table = Table(title="Database Information")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Entries", str(total_entries))
    table.add_row("Events", str(events))
    table.add_row("People", str(people))
    table.add_row("Unique Locations", str(locations))
    table.add_row("Date Range", f"{earliest} to {latest}")
    table.add_row("Database Path", str(db_path))

    console.print(table)

@app.command()
def list_entries(
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
    show_details: bool = typer.Option(
        False,
        "--details",
        "-s",
        help="Show entry details",
    ),
):
    """List all entries in the database."""
    session = get_db_session(db_path)
    entries = session.query(HistoricalEntry).all()

    if not entries:
        print("No entries found in database.")
        return

    table = Table(title="Historical Entries")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Name", style="green")
    table.add_column("Begins", style="yellow")
    table.add_column("Ends", style="yellow")
    table.add_column("Location", style="blue")
    table.add_column("Stories", style="red")
    if show_details:
        table.add_column("Details", style="white", no_wrap=False)

    for entry in entries:
        story_count = len(entry.stories)
        story_text = f"{story_count} stor{'ies' if story_count != 1 else 'y'}" if story_count > 0 else "no stories"
        table.add_row(
            str(entry.id),
            entry.type,
            entry.name,
            str(entry.begins),
            str(entry.ends),
            entry.location,
            story_text,
            (
                f"{entry.details[:50]}..."
                if len(entry.details) > 50 and show_details
                else entry.details if show_details
                else ""
            ),
        )

    console.print(table)

@app.command()
def list_entries_without_stories(
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """List all entries that don't have any associated stories."""
    session = get_db_session(db_path)
    entries = session.query(HistoricalEntry).filter(~HistoricalEntry.stories.any()).all()

    if not entries:
        print("No entries found without stories in database.")
        return

    table = Table(title="Entries Without Stories")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Name", style="green")
    table.add_column("Begins", style="yellow")
    table.add_column("Ends", style="yellow")
    table.add_column("Location", style="blue")

    for entry in entries:
        table.add_row(
            str(entry.id),
            entry.type,
            entry.name,
            str(entry.begins),
            str(entry.ends),
            entry.location,
        )

    console.print(table)

@app.command()
def remove_duplicates(
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """Remove duplicate entries from the database."""
    session = get_db_session(db_path)
    
    # Get all entries
    entries = session.query(HistoricalEntry).all()
    
    # Track seen entries by their key attributes
    seen = set()
    duplicates = []
    
    for entry in entries:
        # Create a tuple of identifying attributes
        entry_key = (entry.name, entry.type, entry.begins, entry.ends, entry.location)
        
        if entry_key in seen:
            duplicates.append(entry)
        else:
            seen.add(entry_key)
    
    # Remove duplicates
    for entry in duplicates:
        session.delete(entry)
    
    session.commit()
    print(f"Removed {len(duplicates)} duplicate entries")

@app.command()
def delete_entries(
    ids: List[int] = typer.Argument(..., help="IDs of entries to delete"),
    db_path: Path = typer.Option(
        "history.db",
        "--db",
        "-d",
        help="Database file path",
        exists=False,
    ),
):
    """Delete specific entries by their IDs."""
    session = get_db_session(db_path)

    # Get entries by IDs
    entries = session.query(HistoricalEntry).filter(HistoricalEntry.id.in_(ids)).all()
    found_ids = {entry.id for entry in entries}
    if not_found := set(ids) - found_ids:
        print(f"Warning: Could not find entries with IDs: {', '.join(map(str, not_found))}")

    # Show entries to be deleted
    if entries:
        print("\nEntries to be deleted:")
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Location")
        table.add_column("Begins")
        table.add_column("Ends")

        for entry in entries:
            table.add_row(
                str(entry.id),
                entry.type,
                entry.name,
                entry.location,
                str(entry.begins),
                str(entry.ends)
            )

        console.print(table)

        # Confirm deletion
        if typer.confirm("\nDelete these entries?"):
            for entry in entries:
                session.delete(entry)
            session.commit()
            print(f"Deleted {len(entries)} entries")
        else:
            print("Deletion cancelled")

@app.command()
def list_stories():
    """List all stories and their entries."""
    session = get_db_session()
    stories = session.query(Story).all()
    
    if not stories:
        print("No stories found in database.")
        return
    
    table = Table(title="Stories")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Entry Count", justify="right")
    
    for story in stories:
        table.add_row(
            str(story.id),
            story.name,
            story.description or "",
            str(len(story.entries))
        )
    
    console.print(table)

@app.command()
def show_story(
    story_id: int = typer.Argument(..., help="ID of the story to show")
):
    """Show details of a specific story and its entries."""
    session = get_db_session()
    story = session.query(Story).filter_by(id=story_id).first()
    
    if not story:
        print(f"Story with ID {story_id} not found.")
        return
    
    # Print story details
    print(f"\nStory: {story.name}")
    if story.description:
        print(f"Description: {story.description}")
    print(f"Color: {story.color or 'Not set'}")
    
    if not story.entries:
        print("\nNo entries in this story.")
        return
    
    # Print entries
    table = Table(title=f"Entries in {story.name}")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Location")
    table.add_column("Begins")
    table.add_column("Ends")
    
    for entry in sorted(story.entries, key=lambda x: x.begins):
        table.add_row(
            str(entry.id),
            entry.type,
            entry.name,
            entry.location,
            str(entry.begins),
            str(entry.ends)
        )
    
    console.print(table)

@app.command()
def create_story(
    name: str = typer.Argument(..., help="Name of the story"),
    description: str = typer.Option(None, "--description", "-d", help="Description of the story"),
    color: str = typer.Option(None, "--color", "-c", help="Color for visualization (e.g., #FF0000)")
):
    """Create a new story."""
    session = get_db_session()
    
    # Check if story already exists
    if session.query(Story).filter_by(name=name).first():
        print(f"Story '{name}' already exists.")
        return
    
    story = Story(name=name, description=description, color=color)
    session.add(story)
    session.commit()
    print(f"Created story '{name}' with ID {story.id}")

@app.command()
def add_to_story(
    story_id: int = typer.Argument(..., help="ID of the story"),
    entry_ids: List[int] = typer.Argument(..., help="IDs of entries to add")
):
    """Add entries to a story."""
    session = get_db_session()
    story = session.query(Story).filter_by(id=story_id).first()
    
    if not story:
        print(f"Story with ID {story_id} not found.")
        return
    
    entries = session.query(HistoricalEntry).filter(HistoricalEntry.id.in_(entry_ids)).all()
    found_ids = {entry.id for entry in entries}
    not_found = set(entry_ids) - found_ids
    
    if not_found:
        print(f"Warning: Could not find entries with IDs: {', '.join(map(str, not_found))}")
    
    for entry in entries:
        if entry not in story.entries:
            story.entries.append(entry)
    
    session.commit()
    print(f"Added {len(entries)} entries to story '{story.name}'")

@app.command()
def remove_from_story(
    story_id: int = typer.Argument(..., help="ID of the story"),
    entry_ids: List[int] = typer.Argument(..., help="IDs of entries to remove")
):
    """Remove entries from a story."""
    session = get_db_session()
    story = session.query(Story).filter_by(id=story_id).first()
    
    if not story:
        print(f"Story with ID {story_id} not found.")
        return
    
    entries = session.query(HistoricalEntry).filter(HistoricalEntry.id.in_(entry_ids)).all()
    found_ids = {entry.id for entry in entries}
    not_found = set(entry_ids) - found_ids
    
    if not_found:
        print(f"Warning: Could not find entries with IDs: {', '.join(map(str, not_found))}")
    
    for entry in entries:
        if entry in story.entries:
            story.entries.remove(entry)
    
    session.commit()
    print(f"Removed {len(entries)} entries from story '{story.name}'")

def main():
    app()

if __name__ == "__main__":
    main()
