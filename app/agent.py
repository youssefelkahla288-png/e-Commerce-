"""Route questions to either a local, no-AI assistant or the OpenAI agent."""

from typing import Literal

from app.offline import answer_local

AssistantMode = Literal["local", "openai"]
_executor = None


def _get_openai_executor():
    """Create the LangChain agent only when OpenAI mode is explicitly selected."""
    global _executor
    if _executor is None:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_openai import ChatOpenAI

        from app.config import settings
        from app.tools import ALL_TOOLS

        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the customer assistant for an online electronics store. "
                    "Use product_search for product questions and faq_lookup for store "
                    "policies. Be friendly and concise.",
                ),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
        _executor = AgentExecutor(agent=agent, tools=ALL_TOOLS, verbose=True)
    return _executor


def ask_agent(message: str, mode: AssistantMode = "local") -> str:
    """Answer locally by default; contact OpenAI only in explicit OpenAI mode."""
    if mode == "local":
        return answer_local(message)
    if mode == "openai":
        result = _get_openai_executor().invoke({"input": message})
        return result["output"]
    raise ValueError("mode must be either 'local' or 'openai'")


if __name__ == "__main__":
    print(ask_agent("How many days do I have to return a product?"))
