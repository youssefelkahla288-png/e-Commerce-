build_vectorstore.py — reads data/faq.md, splits it into chunks, embeds them,
and saves a searchable Chroma vector store to data/vectorstore/.

Run this ONCE (and again whenever you edit faq.md):
    python -m scripts.build_vectorstore
"""

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.config import settings


def main():
    # 1. LOAD the FAQ document
    docs = TextLoader("data/faq.md", encoding="utf-8").load()

    # 2. SPLIT it into chunks (small, focused pieces the search can match)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=75)
    chunks = splitter.split_documents(docs)

    # 3. EMBED + 4. STORE (one call embeds every chunk and saves it to disk)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", api_key=settings.openai_api_key
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.vectorstore_dir,
    )

    print(f"✅ Vector store built with {len(chunks)} chunks at {settings.vectorstore_dir}")


if __name__ == "__main__":
    main()
    