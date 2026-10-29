import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import rag
from app.config import settings
from scripts import build_vectorstore


class RagPipelineTests(unittest.TestCase):
    def test_answers_from_injected_retriever_without_network(self):
        retriever = Mock()
        retriever.invoke.return_value = [
            SimpleNamespace(page_content="Returns are accepted within 14 days.")
        ]
        llm = Mock()
        llm.invoke.return_value = SimpleNamespace(content="You have 14 days to return it.")

        answer = rag.answer_faq(
            "How long can I return an item?", retriever=retriever, llm=llm
        )

        self.assertEqual(answer, "You have 14 days to return it.")
        retriever.invoke.assert_called_once_with("How long can I return an item?")
        prompt = llm.invoke.call_args.args[0]
        self.assertIn("Returns are accepted within 14 days.", prompt)
        self.assertIn("How long can I return an item?", prompt)

    def test_missing_index_fails_before_loading_external_packages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "not-built-yet"
            with patch.object(
                rag, "settings", SimpleNamespace(vectorstore_dir=str(missing_path))
            ):
                with self.assertRaisesRegex(FileNotFoundError, "build_vectorstore"):
                    rag._get_retriever()


class ModelAndPathConfigTests(unittest.TestCase):
    def test_model_ids_are_shared_and_validly_formatted(self):
        self.assertEqual(settings.chat_model, "gpt-4.1-nano")
        self.assertEqual(settings.embedding_model, "text-embedding-3-small")

    def test_faq_source_path_is_project_rooted(self):
        faq_path = build_vectorstore.BASE_DIR / "data" / "faq.md"
        self.assertEqual(faq_path, Path(__file__).resolve().parents[1] / "data" / "faq.md")
        self.assertTrue(faq_path.is_file())


if __name__ == "__main__":
    unittest.main()
