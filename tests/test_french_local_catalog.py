import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import offline
from scripts.create_database import create_database


class FrenchLocalCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "catalog.sqlite3"
        create_database(self.db_path)
        categories = (
            "Laptops",
            "Smartphones",
            "Headphones",
            "Smartwatches",
            "Tablets",
        )
        products = (
            ("Laptop budget", "Laptops", 500),
            ("Laptop premium", "Laptops", 1500),
            ("Smartphone budget", "Smartphones", 700),
            ("Smartphone premium", "Smartphones", 1300),
            ("Headphones budget", "Headphones", 100),
            ("Headphones premium", "Headphones", 300),
            ("Smartwatch budget", "Smartwatches", 150),
            ("Smartwatch premium", "Smartwatches", 400),
            ("Tablet budget", "Tablets", 400),
            ("Tablet premium", "Tablets", 1200),
        )
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.executemany(
                "INSERT INTO categories (name) VALUES (?)",
                ((category,) for category in categories),
            )
            category_ids = {
                name: connection.execute(
                    "SELECT id FROM categories WHERE name = ?", (name,)
                ).fetchone()[0]
                for name in categories
            }
            connection.execute("INSERT INTO brands (name) VALUES ('Example')")
            brand_id = connection.execute(
                "SELECT id FROM brands WHERE name = 'Example'"
            ).fetchone()[0]
            connection.executemany(
                "INSERT INTO products (name, category_id, brand_id, price, stock) "
                "VALUES (?, ?, ?, ?, 5)",
                (
                    (name, category_ids[category], brand_id, price)
                    for name, category, price in products
                ),
            )
        self.settings_patch = patch.object(
            offline, "settings", SimpleNamespace(db_path=str(self.db_path))
        )
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()
        self.temp_dir.cleanup()

    def test_french_category_terms_match_english_catalog_categories(self):
        questions = {
            "ordinateur portable": "Laptop budget",
            "téléphone": "Smartphone budget",
            "écouteurs": "Headphones budget",
            "casque": "Headphones budget",
            "montre": "Smartwatch budget",
            "tablette": "Tablet budget",
        }
        for question, expected_product in questions.items():
            with self.subTest(question=question):
                answer = offline.answer_local(question)
                self.assertIn(expected_product, answer)
                self.assertNotIn("aucun produit correspondant", answer)

    def test_moins_cher_sorts_matching_category_by_lowest_price(self):
        answer = offline.answer_local("ordinateur portable moins cher")

        self.assertLess(answer.index("Laptop budget"), answer.index("Laptop premium"))

    def test_moins_de_price_filters_all_products_to_upper_bound(self):
        answer = offline.answer_local("produits à moins de 1000")

        self.assertIn("Laptop budget", answer)
        self.assertIn("Smartphone budget", answer)
        self.assertNotIn("Laptop premium", answer)
        self.assertNotIn("Smartphone premium", answer)
        self.assertNotIn("Tablet premium", answer)

    def test_english_phone_contact_question_still_uses_faq(self):
        answer = offline.answer_local("What is your phone number?")

        self.assertIn("support@techstore.tn", answer)


if __name__ == "__main__":
    unittest.main()
