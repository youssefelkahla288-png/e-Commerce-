import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.database import run_select
from scripts.create_database import create_database


class DatabaseSchemaTests(unittest.TestCase):
    def test_creates_expected_tables_and_preserves_existing_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.sqlite3"
            create_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection, connection:
                connection.execute("INSERT INTO categories (name) VALUES (?)", ("Laptops",))
                connection.execute("INSERT INTO brands (name) VALUES (?)", ("Example",))
                connection.execute(
                    "INSERT INTO products (name, category_id, brand_id, price, stock) "
                    "VALUES (?, 1, 1, 999.99, 4)",
                    ("Example laptop",),
                )

            # Re-running initialization is safe and must leave rows intact.
            create_database(db_path)
            with patch("app.database.settings", SimpleNamespace(db_path=str(db_path))):
                rows = run_select(
                    "SELECT p.name, c.name AS category, b.name AS brand, p.stock "
                    "FROM products p "
                    "JOIN categories c ON c.id = p.category_id "
                    "JOIN brands b ON b.id = p.brand_id"
                )

            self.assertEqual(
                rows,
                [{"name": "Example laptop", "category": "Laptops", "brand": "Example", "stock": 4}],
            )


if __name__ == "__main__":
    unittest.main()
