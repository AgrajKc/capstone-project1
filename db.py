import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "why.db"

NEW_COLUMNS = ("why_it_happened", "deeper_why", "next_time")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(entries)").fetchall()
    }
    for column in NEW_COLUMNS:
        if column not in existing:
            connection.execute(f"ALTER TABLE entries ADD COLUMN {column} TEXT")

    connection.commit()
    connection.close()


def add_entry(problem, why_it_happened, deeper_why, next_time):
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO entries (
            problem, why_it_happened, deeper_why, next_time, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            problem,
            why_it_happened,
            deeper_why,
            next_time,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    connection.commit()
    connection.close()


def get_all_entries():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, problem, why_it_happened, deeper_why, next_time, created_at
        FROM entries
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()
    connection.close()

    entries = []
    for row in rows:
        created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        entries.append(
            {
                "id": row["id"],
                "problem": row["problem"],
                "why_it_happened": row["why_it_happened"] or "",
                "deeper_why": row["deeper_why"] or "",
                "next_time": row["next_time"] or "",
                "created_at": created.strftime("%d %B %Y, %I:%M %p"),
            }
        )
    return entries
