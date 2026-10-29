import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import offline
from scripts.create_database import create_database


class LocalCatalogSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "catalog.sqlite3"
        create_database(self.db_path)
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("INSERT INTO categories (name) VALUES (?)", ("Ordinateurs portables",))
            connection.execute("INSERT INTO brands (name) VALUES (?)", ("Acme",))
            connection.execute(
                "INSERT INTO products (name, description, category_id, brand_id, price, stock) "
                "VALUES (?, ?, 1, 1, ?, ?)",
                ("SonicWave Laptop", "Ordinateur portable léger", 749.50, 3),
            )
        self.settings_patch = patch.object(
            offline, "settings", SimpleNamespace(db_path=str(self.db_path))
        )
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()
        self.temp_dir.cleanup()

    def test_searches_product_by_name_and_shows_database_price(self):
        answer = offline.answer_local("Recherche par nom le produit SonicWave")

        self.assertIn("SonicWave Laptop", answer)
        self.assertIn("749.50", answer)
        self.assertIn("catégorie : Ordinateurs portables", answer)
        self.assertIn("marque : Acme", answer)

    def test_searches_by_category(self):
        answer = offline.answer_local("Trouve les produits de la catégorie Ordinateurs portables")

        self.assertIn("SonicWave Laptop", answer)
        self.assertIn("749.50", answer)

    def test_searches_by_brand(self):
        answer = offline.answer_local("Quels produits de la marque Acme sont disponibles ?")

        self.assertIn("SonicWave Laptop", answer)
        self.assertIn("749.50", answer)

    def test_returns_clear_message_when_search_has_no_matches(self):
        answer = offline.answer_local("Recherche le produit introuvable ZXQ-999")

        self.assertIn("aucun produit correspondant", answer)
        self.assertNotIn("SonicWave Laptop", answer)

    def test_returns_clear_message_when_database_has_no_product_table(self):
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("DROP TABLE products")

        answer = offline.answer_local("Recherche un produit")

        self.assertIn("pas encore de table produits", answer)

    def test_returns_clear_message_for_unreadable_database(self):
        self.db_path.write_bytes(b"not a sqlite database")

        answer = offline.answer_local("Recherche un produit")

        self.assertIn("n'est pas encore prête", answer)

    def test_missing_database_is_not_created(self):
        missing_path = Path(self.temp_dir.name) / "missing.sqlite3"
        with patch.object(offline, "settings", SimpleNamespace(db_path=str(missing_path))):
            answer = offline.answer_local("Recherche un produit")

        self.assertIn("ne contient pas encore de produits", answer)
        self.assertFalse(missing_path.exists())


if __name__ == "__main__":
    unittest.main()
