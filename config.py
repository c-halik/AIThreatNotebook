import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
KB_DIR = ROOT_DIR / "knowledge_base"
NOTEBOOK_DIR = KB_DIR / "notebook"
DOCS_DIR = KB_DIR / "docs"
CHROMA_DIR = ROOT_DIR / ".chroma"

# Defaults to local dev (Ollama running on the host). In docker-compose,
# this is overridden to point at the "ollama" service instead.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

LLM_MODEL = "llama3:8b"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "security_kb"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
RETRIEVAL_K = 4

# --- Web search fallback -----------------------------------------------
# When the local knowledge base has no good match for a question, the app
# can fall back to a live web search restricted to these trusted security
# news/reference sites (edit freely).
WEB_SEARCH_ENABLED_DEFAULT = True
TRUSTED_SECURITY_SITES = [
    "darkreading.com",
    "thehackernews.com",
    "bleepingcomputer.com",
    "krebsonsecurity.com",
    "securityweek.com",
    "owasp.org",
    "attack.mitre.org",
    "atlas.mitre.org",
]
WEB_MAX_RESULTS = 5
# Chroma relevance score (cosine-based) is normalized to [0, 1], higher = more
# similar. If the best match scores below this, treat the KB as "no
# information" and fall back to web search. With a small/starter knowledge
# base, scores for topically-adjacent-but-not-actually-covered questions can
# still land in the 0.4-0.6 range - tune this threshold up as your knowledge
# base grows and you observe real score distributions for good vs. bad
# matches (print `best_score` from `rag/retrieval.py` while testing).
KB_RELEVANCE_THRESHOLD = 0.55

# A static knowledge base can never answer "what just happened" questions, no
# matter how high the embedding similarity scores - so these keywords force
# a web search regardless of KB relevance.
TIME_SENSITIVE_KEYWORDS = [
    "latest", "recent", "newest", "current", "today", "this week",
    "breaking", "just disclosed", "just released", "new cve", "zero-day",
]

SYSTEM_PROMPT = """You are a security research assistant specializing in AI security \
and agentic AI security. You answer questions using the reference material provided \
in the context below. That material may come from two places, each labeled accordingly:
1. The user's own curated knowledge base and notebook.
2. Live web search results from trusted security news/reference sites, used only when \
the knowledge base had no good answer.

Rules:
- Ground your answers in the provided context when it is relevant.
- Always distinguish which source type you're drawing from (knowledge base vs. web) and \
cite the specific source file or URL for each piece of information you use.
- If web results are present, treat them as current/external information, not the user's \
own vetted notes - flag anything time-sensitive or that should be double-checked.
- Never claim you searched the web or checked external sources unless a "Context from \
web search" section actually appears below - if it's absent, you were not given web results.
- If neither source covers the question, say so clearly and then answer from general \
knowledge, noting that it isn't grounded in either source.
- Be precise and technical; the user is building an AI security lab and expects rigor.
"""
