#!/usr/bin/env python3
"""Database management script."""
from pathlib import Path

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ingest.base import clear_database
from ingest.csv_ingest import load_from_csv
from ingest.markdown_ingest import load_from_markdown
from models import HistoricalEntry, Base

app = typer.Typer(help="Manage historical timeline database")
console = Console()

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
):
    """List all entries in the database."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

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
    table.add_column("Details", style="white", no_wrap=False)

    for entry in entries:
        table.add_row(
            str(entry.id),
            entry.type,
            entry.name,
            str(entry.begins),
            str(entry.ends),
            entry.location,
            (entry.details[:50] + "...") if len(entry.details) > 50 else entry.details
        )

    console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()
