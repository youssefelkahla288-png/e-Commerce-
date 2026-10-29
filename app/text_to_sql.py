"""
text_to_sql.py — FEATURE 1.

Turns a natural-language product question into a SQL query, runs it, and turns the
result back into a friendly sentence. Three steps, clearly separated so each is
easy to understand and test.
"""

import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.database import run_select

# Load the schema once, when this file is first imported.
with open(settings.schema_path, "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)

# temperature=0 => the model is as predictable/factual as possible. Good for SQL.
llm = ChatOpenAI(
    model=settings.chat_model, temperature=0, api_key=settings.openai_api_key
)


# ---------- STEP 1 PROMPT: write the SQL ----------
# The ONLY curly-brace {placeholders} here are our real variables. Keep it that way,
# or PromptTemplate will try to read stray braces as variables and crash.
SQL_PROMPT = PromptTemplate.from_template(
    """You are an expert data assistant for an online electronics store.
Write ONE valid SQLite SELECT query that answers the user's question.

Rules:
- Only produce a SELECT query. Never write INSERT, UPDATE, DELETE, or DROP.
- Only use the tables and columns in the schema below.
- If the user asks about a category or brand by name, join to the categories/brands tables.
- The schema gives "sample_values" for text columns. Prefer matching those exactly.
- Match text case-insensitively and allow singular/plural wording: compare with LIKE
  and wrap the value in %, e.g.  WHERE lower(c.name) LIKE lower('%laptop%').
- Return ONLY the SQL query, with no explanation and no markdown fences.

Database schema (JSON):
{schema}

User question:
{question}

SQL query:"""
)

# ---------- STEP 3 PROMPT: describe the results ----------
ANSWER_PROMPT = PromptTemplate.from_template(
    """You are a friendly shopping assistant for an electronics store.
Turn the raw database results into a short, helpful, natural answer.

Guidelines:
- Only use the data provided. Never invent products, prices, or specs.
- If the results are empty, say we couldn't find a match and suggest they try different terms.
- Keep it conversational and concise. Mention product names and prices when relevant.

User question:
{question}

Raw database results:
{results}

Your answer:"""
)


def _clean_sql(raw: str) -> str:
    """
    Tidy the model's output: remove markdown fences (```sql ... ```) and any
    single trailing semicolon. We strip the trailing ';' so a normal query like
    'SELECT ...;' isn't wrongly blocked by our safety check below.
    """
    return raw.replace("```sql", "").replace("```", "").strip().rstrip(";").strip()


def _is_safe_select(sql: str) -> bool:
    """
    A simple safety gate: allow ONLY a single SELECT statement.
    The LLM is usually well-behaved, but we NEVER trust generated code blindly.
    - Must start with SELECT (so it can only read).
    - No writing keywords (insert/update/delete/drop/alter/create).
    - No ';' left inside: after _clean_sql removed the trailing one, a remaining
      ';' means someone tried to sneak in a SECOND statement (stacked injection).
    """
    lowered = sql.lower()
    starts_with_select = lowered.startswith("select")
    # Whole-word match so a legit column like "created_at" doesn't trip the "create" rule.
    has_write_keyword = bool(
        re.search(r"\b(insert|update|delete|drop|alter|create|truncate)\b", lowered)
    )
    has_semicolon = ";" in lowered
    return starts_with_select and not has_write_keyword and not has_semicolon


def search_products(question: str) -> str:
    """The full pipeline: question -> SQL -> rows -> friendly answer."""
    # STEP 1: ask the LLM for SQL
    raw_sql = (SQL_PROMPT | llm | StrOutputParser()).invoke(
        {"schema": json.dumps(SCHEMA), "question": question}
    )
    sql = _clean_sql(raw_sql)
    print(f"[text_to_sql] generated SQL: {sql}")   # visible in the terminal for debugging

    # STEP 2: safety check, then run it
    if not _is_safe_select(sql):
        return "I can only look up product information, so I couldn't run that request."
    try:
        rows = run_select(sql)
    except Exception as e:
        return f"Je n'ai pas réussi à interroger la base ({e}). Reformule ta question."

    # STEP 3: ask the LLM to describe the rows in plain language
    answer = (ANSWER_PROMPT | llm | StrOutputParser()).invoke(
        {"question": question, "results": rows if rows else "The query returned no rows."}
    )
    return answer


# Lets us test this file ALONE, without the agent or UI. Run: python -m app.text_to_sql
if __name__ == "__main__":
    print(search_products("What Apple products do you have under 1500 dollars?"))
