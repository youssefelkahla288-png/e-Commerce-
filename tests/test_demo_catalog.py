import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import agent, offline
from app.config import BASE_DIR
from scripts.create_demo_catalog import create_demo_catalog


class DemoCatalogTests(unittest.TestCase):
    def test_creates_fictional_catalog_and_local_search_returns_catalog_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))):
                answer = offline.answer_local("Recherche par nom Asterion Nova")

        self.assertIn("FICTIF - Asterion Nova 14", answer)
        self.assertIn("749.50", answer)
        self.assertIn("Ordinateurs fictifs", answer)
        self.assertIn("Asterion (marque fictive)", answer)

    def test_plural_product_question_matches_singular_catalog_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))):
                answer = offline.answer_local("Quels ordinateurs portables sont disponibles ?")

        self.assertIn("FICTIF - Asterion Nova 14", answer)
        self.assertIn("749.50", answer)
        self.assertIn("Ordinateurs fictifs", answer)
        self.assertNotIn("Sonoria Pulse", answer)

    def test_headphone_synonym_searches_audio_category(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))):
                answer = offline.answer_local("Montre-moi les casques audio")

        self.assertIn("FICTIF - Sonoria Pulse", answer)
        self.assertIn("89.90", answer)
        self.assertIn("Audio fictif", answer)
        self.assertNotIn("aucun produit correspondant", answer)

    def test_natural_availability_questions_search_the_identified_catalog_product(self):
        questions = (
            "As-tu le Sonoria Pulse ?",
            "Avez-vous le Sonoria Pulse ?",
            "Est-ce que le Sonoria Pulse est disponible ?",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))):
                answers = [offline.answer_local(question) for question in questions]

        for answer in answers:
            with self.subTest(answer=answer):
                self.assertIn("FICTIF - Sonoria Pulse", answer)
                self.assertIn("89.90", answer)
                self.assertIn("Audio fictif", answer)

    def test_availability_wording_about_shipping_still_routes_to_faq(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))):
                answer = offline.answer_local("Avez-vous une livraison express ?")

        self.assertIn("Réponse issue de la FAQ locale", answer)
        self.assertIn("15 dinars", answer)

    def test_demo_searches_by_name_category_and_brand_through_local_chatbot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))), patch.object(
                agent, "_get_openai_executor", side_effect=AssertionError("OpenAI must not run")
            ):
                by_name = agent.ask_agent("Recherche par nom Asterion Nova")
                by_category = agent.ask_agent(
                    "Trouve les produits de la catégorie Ordinateurs fictifs"
                )
                by_brand = agent.ask_agent(
                    "Quels produits de la marque Sonoria sont disponibles ?"
                )

        self.assertIn("FICTIF - Asterion Nova 14", by_name)
        self.assertNotIn("FICTIF - Asterion Mini", by_name)
        self.assertIn("FICTIF - Asterion Nova 14", by_category)
        self.assertNotIn("FICTIF - Sonoria Pulse", by_category)
        self.assertIn("FICTIF - Sonoria Pulse", by_brand)
        self.assertIn("89.90", by_brand)
        self.assertIn("Audio fictif", by_brand)
        self.assertIn("Sonoria (marque fictive)", by_brand)

    def test_demo_filters_by_maximum_price_without_matching_amount_as_product_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "demo.sqlite3"
            create_demo_catalog(demo_path)
            with patch.object(offline, "settings", SimpleNamespace(db_path=str(demo_path))), patch.object(
                agent, "_get_openai_executor", side_effect=AssertionError("OpenAI must not run")
            ):
                answer = agent.ask_agent("Quels produits coûtent moins de 100 dinars ?")

        self.assertIn("FICTIF - Sonoria Pulse", answer)
        self.assertIn("89.90", answer)
        self.assertIn("FICTIF - Asterion Mini", answer)
        self.assertIn("24.00", answer)
        self.assertNotIn("FICTIF - Asterion Nova 14", answer)

    def test_extracts_decimal_maximum_price(self):
        bound, remaining = offline._extract_max_price(
            "Produits avec un prix maximum de 89,90 dinars"
        )

        self.assertEqual(bound, 89.9)
        self.assertNotIn("89,90", remaining)

    def test_refuses_to_overwrite_existing_demo_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "existing.sqlite3"
            original_bytes = b"keep this file unchanged"
            demo_path.write_bytes(original_bytes)

            with self.assertRaises(FileExistsError):
                create_demo_catalog(demo_path)

            self.assertEqual(demo_path.read_bytes(), original_bytes)

    def test_never_targets_the_real_catalog_database(self):
        with self.assertRaisesRegex(ValueError, "cannot target the real ecommerce.db"):
            create_demo_catalog(BASE_DIR / "ecommerce.db")


if __name__ == "__main__":
    unittest.main()
