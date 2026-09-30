"""
extract_schema.py — writes the database structure (tables + columns) to schema.json.
Run once after building the DB:  python -m scripts.extract_schema
"""

import json
import sqlite3

from app.config import settings


def main():
    connection = sqlite3.connect(settings.db_path)
    cursor = connection.cursor()

    # Ask SQLite for the list of tables (ignoring its internal ones).
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        # PRAGMA table_info returns one row per column:
        # (id, name, type, notnull, default, is_primary_key)
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        table_schema = []
        for col in columns:
            col_name, col_type = col[1], col[2]
            entry = {"column": col_name, "type": col_type}

            # For text columns, also include a few real values. This is what stops
            # the LLM guessing 'headphones' when the DB actually stores 'Headphones'.
            if "CHAR" in col_type.upper() or "TEXT" in col_type.upper():
                cursor.execute(
                    f'SELECT DISTINCT "{col_name}" FROM "{table}" '
                    f'WHERE "{col_name}" IS NOT NULL LIMIT 5'
                )
                entry["sample_values"] = [row[0] for row in cursor.fetchall()]

            table_schema.append(entry)

        schema[table] = table_schema

    connection.close()

    with open(settings.schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"✅ Schema written to {settings.schema_path}")
    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
