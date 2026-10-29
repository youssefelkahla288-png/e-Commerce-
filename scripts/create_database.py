"""Create the SQLite tables used by the product-search pipeline.

Run from the project root with ``python -m scripts.create_database``. Existing
tables and rows are preserved; this script only creates missing tables/indexes.
"""

import random
import sqlite3
from pathlib import Path

from faker import Faker

from app.config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    brand_id INTEGER,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    rating REAL CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)),
    num_reviews INTEGER NOT NULL DEFAULT 0 CHECK (num_reviews >= 0),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
"""


def create_database(db_path: str | Path | None = None) -> None:
    """Create missing tables in ``db_path`` or the configured database."""
    path = Path(db_path or settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_SQL)
    finally:
        connection.close()


def main() -> None:
    random.seed(42)
    Faker.seed(42)
    create_database()
    print(f"SQLite schema is ready at {settings.db_path}")


if __name__ == "__main__":
    main()
