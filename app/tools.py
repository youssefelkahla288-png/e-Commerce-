"""
tools.py — wraps our two features as "tools" the agent can choose from.

A tool = a normal function + a clear description. The agent reads the descriptions
to decide which tool fits the user's message. Good descriptions = good choices.
"""

from langchain_core.tools import tool

from app.text_to_sql import search_products
from app.rag import answer_faq


@tool
def product_search(question: str) -> str:
    """Use for questions about PRODUCTS: prices, stock, brands, categories,
    ratings, or finding/comparing specific items (e.g. "cheapest laptop",
    "Apple products under 1500", "is the Sony headphone in stock")."""
    return search_products(question)


@tool
def faq_lookup(question: str) -> str:
    """Use for questions about STORE POLICIES: shipping, returns, refunds,
    warranty, payment options, or contact details (e.g. "how do returns work",
    "do you offer free shipping", "can I pay in installments")."""
    return answer_faq(question)


# The list the agent will be given.
ALL_TOOLS = [product_search, faq_lookup]