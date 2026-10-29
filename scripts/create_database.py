"""Create the SQLite tables used by the product-search pipeline.

Run from the project root with ``python -m scripts.create_database``. Existing
tables and rows are preserved; this script only creates missing tables/indexes.
"""

import argparse
import random
import sqlite3
from contextlib import closing
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

SEED_BRANDS = ("Apple", "Samsung", "Sony", "Dell", "Bose")
SEED_CATEGORIES = (
    "Smartphones",
    "Laptops",
    "Headphones",
    "Tablets",
    "Smartwatches",
)


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


def seed_database(db_path: str | Path | None = None) -> None:
    """Insert 40 reproducible fictional products without duplicating seeded rows."""
    random.seed(42)
    Faker.seed(42)
    path = Path(db_path or settings.db_path)
    fake = Faker()
    fake.seed_instance(42)

    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executemany(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            ((name,) for name in SEED_CATEGORIES),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO brands (name) VALUES (?)",
            ((name,) for name in SEED_BRANDS),
        )

        category_ids = {
            name: connection.execute(
                "SELECT id FROM categories WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in SEED_CATEGORIES
        }
        brand_ids = {
            name: connection.execute(
                "SELECT id FROM brands WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in SEED_BRANDS
        }
        existing_names = {
            row[0] for row in connection.execute("SELECT name FROM products")
        }

        for index in range(1, 41):
            brand = random.choice(SEED_BRANDS)
            category = random.choice(SEED_CATEGORIES)
            name = f"{brand} {category} Fictif {index:02d}"
            description = (
                f"Produit fictif de démonstration : {fake.sentence(nb_words=6)}"
            )
            price = round(random.uniform(80, 2000), 2)
            stock = random.randint(0, 40)
            rating = round(random.uniform(3, 5), 1)
            num_reviews = random.randint(0, 500)
            if name in existing_names:
                continue
            connection.execute(
                "INSERT INTO products "
                "(name, description, category_id, brand_id, price, stock, rating, num_reviews) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    description,
                    category_ids[category],
                    brand_ids[brand],
                    price,
                    stock,
                    rating,
                    num_reviews,
                ),
            )
            existing_names.add(name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize the product catalogue database."
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="insert 40 reproducible fictional products",
    )
    args = parser.parse_args()

    create_database()
    if args.seed:
        seed_database()
    print(f"SQLite schema is ready at {settings.db_path}")


if __name__ == "__main__":
    main()
