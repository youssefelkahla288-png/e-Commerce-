```
  question
     │
     ▼
  (1) retrieve  ───► find the top matching chunks in the vector store
     │
     ▼
  (2) augment   ───► stuff those chunks into the prompt (the context)
     │
     ▼
  (3) generate  ───► the LLM answers using ONLY that context
```

Create **`app/rag.py`**:

```python
"""
rag.py — FEATURE 2: answer store-policy questions from data/faq.md.

This is the RAG pipeline you built in Colab, now as a reusable function:
  question -> search the vector store -> stuff chunks into a prompt -> grounded answer.
The vector store must already exist (run: python -m scripts.build_vectorstore).
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings

# Open the vector store we built on disk (read-only use here).
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
_store = Chroma(persist_directory=settings.vectorstore_dir, embedding_function=_embeddings)
_retriever = _store.as_retriever(search_kwargs={"k": 3})

_llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0, api_key=settings.openai_api_key)

# The grounding rule: answer ONLY from the retrieved context, admit when it's not there.
_RAG_PROMPT = PromptTemplate.from_template(
    """You are a helpful support agent for an electronics store.
Answer the question using ONLY the context below.
If the answer is not in the context, say you don't have that information and suggest
contacting support. Keep it short and friendly.

Context:
{context}

Question:
{question}

Answer:"""
)


def answer_faq(question: str) -> str:
    """question -> retrieve chunks -> grounded answer."""
    docs = _retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    print(f"[rag] retrieved {len(docs)} chunks")   # visible in the terminal for debugging
    return (_RAG_PROMPT | _llm | StrOutputParser()).invoke(
        {"context": context, "question": question}
    )


# Test this file ALONE:  python -m app.rag
if __name__ == "__main__":
    print(answer_faq("How many days do I have to return something?"))