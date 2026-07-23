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


def retrieve_with_relevance(query: str, k: int = config.RETRIEVAL_K):
    """Retrieve up to `k` candidate chunks, then keep only the ones scoring at
    or above MATCH_RELEVANCE_THRESHOLD - i.e. every plausible vendor match,
    not just a fixed top-N. Also returns the best score across *all*
    candidates (even filtered-out ones) so callers can decide whether a web
    search fallback is warranted."""
    if not config.CHROMA_DIR.exists():
        return [], 0.0
    vectorstore = load_vectorstore()
    scored = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    if not scored:
        return [], 0.0
    best_score = max(score for _doc, score in scored)
    matches = [doc for doc, score in scored if score >= config.MATCH_RELEVANCE_THRESHOLD]
    return matches, best_score


def format_context(docs) -> str:
    if not docs:
        return "(no matching knowledge base entries found)"
    blocks = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)
