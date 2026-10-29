"""Answer store-policy questions using the persisted FAQ vector store."""

from pathlib import Path
from typing import Any

from app.config import settings

_RAG_PROMPT = """You are a helpful support agent for an electronics store.
Answer the question using ONLY the context below.
If the answer is not in the context, say you don't have that information and suggest
contacting support. Keep it short and friendly.

Context:
{context}

Question:
{question}

Answer:"""


def _get_retriever() -> Any:
    """Open the existing Chroma index when a FAQ question is asked."""
    vectorstore_dir = Path(settings.vectorstore_dir)
    if not vectorstore_dir.is_dir():
        raise FileNotFoundError(
            "FAQ index not found. Build it with `python -m scripts.build_vectorstore`."
        )

    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model, api_key=settings.openai_api_key
    )
    store = Chroma(
        persist_directory=str(vectorstore_dir), embedding_function=embeddings
    )
    return store.as_retriever(search_kwargs={"k": 3})


def answer_faq(
    question: str,
    *,
    retriever: Any = None,
    llm: Any = None,
) -> str:
    """Retrieve relevant FAQ text and generate a grounded response.

    Dependencies can be injected to test the pipeline without network access.
    """
    if retriever is None:
        retriever = _get_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    if llm is None:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.chat_model, temperature=0, api_key=settings.openai_api_key
        )

    response = llm.invoke(
        _RAG_PROMPT.format(question=question, context=context)
    )
    return response.content if hasattr(response, "content") else str(response)


if __name__ == "__main__":
    print(answer_faq("How many days do I have to return something?"))
