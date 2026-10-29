"""Create a separate SQLite catalog containing clearly fictional demo entries.

Run from the project root with ``python -m scripts.create_demo_catalog``.
The script refuses to overwrite an existing file. It never targets ecommerce.db.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from app.config import BASE_DIR
from scripts.create_database import create_database

DEMO_DB_PATH = BASE_DIR / "data" / "demo_ecommerce.db"

DEMO_CATEGORIES = (
    "Ordinateurs fictifs",
    "Audio fictif",
    "Accessoires fictifs",
)
DEMO_BRANDS = (
    "Asterion (marque fictive)",
    "Sonoria (marque fictive)",
)
DEMO_PRODUCTS = (
    ("FICTIF - Asterion Nova 14", "Ordinateur portable fictif de démonstration", "Ordinateurs fictifs", "Asterion (marque fictive)", 749.50, 8),
    ("FICTIF - Sonoria Pulse", "Casque audio fictif de démonstration", "Audio fictif", "Sonoria (marque fictive)", 89.90, 12),
    ("FICTIF - Asterion Mini", "Accessoire fictif de démonstration", "Accessoires fictifs", "Asterion (marque fictive)", 24.00, 20),
)


def create_demo_catalog(db_path: str | Path = DEMO_DB_PATH) -> Path:
    """Create the demo catalog at a new path, never replacing an existing file."""
    path = Path(db_path)
    if path.resolve() == (BASE_DIR / "ecommerce.db").resolve():
        raise ValueError("The demo catalog cannot target the real ecommerce.db")
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing demo database: {path}")

    create_database(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            ((name,) for name in DEMO_CATEGORIES),
        )
        connection.executemany(
            "INSERT INTO brands (name) VALUES (?)",
            ((name,) for name in DEMO_BRANDS),
        )
        category_ids = {
            name: connection.execute(
                "SELECT id FROM categories WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in DEMO_CATEGORIES
        }
        brand_ids = {
            name: connection.execute(
                "SELECT id FROM brands WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in DEMO_BRANDS
        }
        connection.executemany(
            "INSERT INTO products (name, description, category_id, brand_id, price, stock) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                (name, description, category_ids[category], brand_ids[brand], price, stock)
                for name, description, category, brand, price, stock in DEMO_PRODUCTS
            ),
        )
    return path


def main() -> None:
    path = create_demo_catalog()
    print(f"Fictional demo catalog created at {path}")
    print("All names, brands, categories, and prices in this database are fictional.")


if __name__ == "__main__":
    main()
