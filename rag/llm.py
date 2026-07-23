from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

import config
from rag.retrieval import format_context
from rag.websearch import format_web_context


def get_llm() -> ChatOllama:
    return ChatOllama(model=config.LLM_MODEL, base_url=config.OLLAMA_BASE_URL, temperature=0.2)


def answer_stream(question: str, history: list[tuple[str, str]], docs, web_results=None):
    """Yield response chunks for `question`, grounded in `docs` (already
    retrieved from the knowledge base) and, optionally, `web_results` (already
    retrieved from the web search fallback).

    `history` is a list of (role, content) tuples for prior turns, role is
    "user" or "assistant".
    """
    kb_context = format_context(docs)
    prompt_sections = [f"Context from knowledge base:\n\n{kb_context}"]

    if web_results is not None:
        web_context = format_web_context(web_results)
        prompt_sections.append(f"Context from web search (trusted security sites):\n\n{web_context}")

    messages = [SystemMessage(content=config.SYSTEM_PROMPT)]
    for role, content in history:
        messages.append(HumanMessage(content=content) if role == "user" else SystemMessage(content=content))

    prompt = "\n\n".join(prompt_sections) + f"\n\nQuestion: {question}"
    messages.append(HumanMessage(content=prompt))

    llm = get_llm()
    for chunk in llm.stream(messages):
        yield chunk.content
