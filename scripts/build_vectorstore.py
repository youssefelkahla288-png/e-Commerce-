"""
build_vectorstore.py — reads data/faq.md, splits it into chunks, embeds them,
and saves a searchable Chroma vector store to data/vectorstore/.

Run this ONCE (and again whenever you edit faq.md):
    python -m scripts.build_vectorstore
"""

from pathlib import Path
import shutil

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent


def build_vectorstore():
    """Build the FAQ index. This function is the only place that calls OpenAI."""
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    # 1. LOAD the FAQ document
    # 1. LOAD the FAQ document
    docs = TextLoader(settings.faq_path, encoding="utf-8").load()

    # 2. SPLIT it into chunks (small, focused pieces the search can match)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=75)
    chunks = splitter.split_documents(docs)

    # 3. EMBED + 4. STORE (one call embeds every chunk and saves it to disk)
    vectorstore_dir = Path(settings.vectorstore_dir)
    if vectorstore_dir.is_dir():
        shutil.rmtree(vectorstore_dir)

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model, api_key=settings.openai_api_key
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.vectorstore_dir,
    )

    print(f"✅ Vector store built with {len(chunks)} chunks at {settings.vectorstore_dir}")


def main():
    build_vectorstore()


if __name__ == "__main__":
    main()
