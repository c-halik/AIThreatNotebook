from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import config


def load_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(model=config.EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(config.CHROMA_DIR),
    )


def retrieve(query: str, k: int = config.RETRIEVAL_K):
    if not config.CHROMA_DIR.exists():
        return []
    vectorstore = load_vectorstore()
    return vectorstore.similarity_search(query, k=k)


def retrieve_with_relevance(query: str, k: int = config.RETRIEVAL_K):
    """Like `retrieve`, but also returns the best relevance score (0-1, higher
    is better) so callers can decide whether the knowledge base actually has
    a good answer or a web search fallback is warranted."""
    if not config.CHROMA_DIR.exists():
        return [], 0.0
    vectorstore = load_vectorstore()
    scored = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    if not scored:
        return [], 0.0
    docs = [doc for doc, _score in scored]
    best_score = max(score for _doc, score in scored)
    return docs, best_score


def format_context(docs) -> str:
    if not docs:
        return "(no matching knowledge base entries found)"
    blocks = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)
