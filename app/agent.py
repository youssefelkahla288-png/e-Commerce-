"""
agent.py — the agent that reads the user's message and picks the right tool.

It uses LangChain's tool-calling agent: we give it our tools (from tools.py) and a
short system prompt, and it decides—per message—whether to call product_search,
faq_lookup, or just answer directly.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.config import settings
from app.tools import ALL_TOOLS

_llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0, api_key=settings.openai_api_key)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the customer assistant for an online electronics store. "
            "Use product_search for questions about products (prices, stock, brands). "
            "Use faq_lookup for questions about policies (shipping, returns, warranty, payment). "
            "If a tool returns the answer, reply based on it. Be friendly and concise.",
        ),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),  # where the agent keeps its tool-use steps
    ]
)

_agent = create_tool_calling_agent(_llm, ALL_TOOLS, _PROMPT)
_executor = AgentExecutor(agent=_agent, tools=ALL_TOOLS, verbose=True)


def ask_agent(message: str) -> str:
    """Send a user message to the agent and return its final answer."""
    result = _executor.invoke({"input": message})
    return result["output"]


# Test this file ALONE:  python -m app.agent
if __name__ == "__main__":
    print(ask_agent("What is the cheapest laptop you have?"))
    print("-" * 40)
    print(ask_agent("How many days do I have to return a product?"))