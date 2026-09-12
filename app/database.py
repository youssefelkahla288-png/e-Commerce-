"""
database.py — the ONLY place that talks to the database.

Why a helper file? Every feature that needs data goes through here, so if we ever
change databases (SQLite -> Postgres), we fix it in one file, not ten.
"""

import sqlite3

from app.config import settings


def get_connection():
    """Open a connection to our SQLite file."""
    connection = sqlite3.connect(settings.db_path)
    # row_factory = Row makes each row behave like a dictionary: row["price"]
    # instead of row[4]. Much easier to read.
    connection.row_factory = sqlite3.Row
    return connection


def run_select(query: str):
    """
    Run a read-only SELECT query and return a list of dictionaries.
    We open, read, and always close — even if something goes wrong (finally).
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]   # convert Row objects to plain dicts
    finally:
        connection.close()
```git