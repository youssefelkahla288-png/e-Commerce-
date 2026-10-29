import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import agent, offline


class OfflineAssistantTests(unittest.TestCase):
    def test_default_mode_answers_from_faq_without_openai(self):
        with patch.object(
            agent, "_get_openai_executor", side_effect=AssertionError("OpenAI was called")
        ):
            answer = agent.ask_agent("How many days do I have to return a product?")

        self.assertIn("14 jours", answer)
        self.assertIn("boîte d’origine", answer)
        self.assertIn("FAQ locale", answer)

    def test_express_delivery_price_is_french_and_exact(self):
        answer = offline.answer_local("Combien coûte la livraison express ?")

        self.assertIn("15 dinars", answer)
        self.assertIn("le lendemain", answer)
        self.assertNotIn("15,", answer)

    def test_paraphrased_arrival_question_preserves_delivery_times(self):
        answer = offline.answer_local("En combien de jours ma commande arrive-t-elle ?")

        self.assertIn("2 à 4 jours ouvrés", answer)
        self.assertIn("le lendemain", answer)
        self.assertIn("15 dinars", answer)

    def test_free_standard_delivery_keeps_order_threshold(self):
        answer = offline.answer_local("La livraison est-elle gratuite ?")

        self.assertIn("gratuite pour les commandes de plus de 200 dinars", answer)
        self.assertIn("ne précise pas son tarif", answer)

    def test_faq_topics_are_answered_in_french_with_source_values(self):
        answers = {
            "Quels sont les délais de remboursement ?": ("14 jours", "5 jours ouvrés"),
            "Quelle garantie pour un produit reconditionné ?": ("6 mois", "30 jours"),
            "Puis-je payer en plusieurs fois ?": ("3 fois", "900 dinars"),
            "Comment contacter le support ?": ("71 234 567", "9 h à 19 h"),
        }
        for question, expected_facts in answers.items():
            with self.subTest(question=question):
                answer = offline.answer_local(question)
                for fact in expected_facts:
                    self.assertIn(fact, answer)

    def test_product_query_with_empty_database_does_not_create_or_change_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "ecommerce.db"
            with patch.object(
                offline, "settings", SimpleNamespace(db_path=str(db_path))
            ):
                answer = offline.answer_local("What is the cheapest laptop?")

            self.assertIn("ne contient pas encore de produits", answer)
            self.assertFalse(db_path.exists())

    def test_openai_is_used_only_when_explicitly_selected(self):
        executor = SimpleNamespace(invoke=lambda payload: {"output": "Mocked answer"})
        with patch.object(agent, "_get_openai_executor", return_value=executor) as factory:
            answer = agent.ask_agent("A question", mode="openai")

        self.assertEqual(answer, "Mocked answer")
        factory.assert_called_once_with()

    def test_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "mode must be"):
            agent.ask_agent("A question", mode="unknown")


if __name__ == "__main__":
    unittest.main()
