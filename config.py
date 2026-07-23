import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
KB_DIR = ROOT_DIR / "knowledge_base"
NOTEBOOK_DIR = KB_DIR / "notebook"
DOCS_DIR = KB_DIR / "docs"
CHROMA_DIR = ROOT_DIR / ".chroma"
TEST_DATA_DIR = ROOT_DIR / "test_data"
TEST_FILES_DIR = TEST_DATA_DIR / "files"

# Defaults to local dev (Ollama running on the host). In docker-compose,
# this is overridden to point at the "ollama" service instead.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

LLM_MODEL = "llama3:8b"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "security_kb"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
# How many candidate chunks to pull from Chroma before relevance-filtering.
# Set higher than a typical RAG default because the use case here is
# "which of my vendor notes address this requirement" - you want every
# plausible vendor considered, not just the single closest match.
RETRIEVAL_K = 10
# Of those candidates, only ones scoring at or above this are treated as a
# real match and shown to the model/user. Without this, retrieval always
# returns exactly RETRIEVAL_K chunks even when most are irrelevant padding.
# Separate from KB_RELEVANCE_THRESHOLD below (that one gates the web-search
# fallback; this one gates which vendor matches get surfaced at all) - tune
# both once you've loaded real vendor notes and can see actual score spreads.
MATCH_RELEVANCE_THRESHOLD = 0.5

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

SYSTEM_PROMPT = """You are a research assistant for a security solutions architect who \
evaluates AI security vendor tools (e.g. Noma Security, Palo Alto Prisma AIRS, Wiz, and \
others) against customer requirements, and shares findings with other companies to help \
them meet their technology requirements.

The context below comes from two places, each labeled accordingly:
1. The architect's own vendor evaluation notes and notebook - one file per vendor/product.
2. Live web search results from trusted security news/reference sites, used only when \
the notes had no good answer.

When asked about a requirement or capability:
- Identify every vendor in the knowledge base whose notes address it - do not stop at the \
single closest match. List each one.
- For each vendor, cite the specific feature/capability described and the source file \
(which is the vendor/product name).
- If multiple vendors cover the same capability, briefly note how their approaches differ \
if the notes describe that.
- If nothing in the knowledge base addresses the requirement, say so clearly before falling \
back to web results (if provided) or general knowledge.

Other rules:
- Always distinguish which source type you're drawing from (knowledge base vs. web) and \
cite the specific source file or URL for each piece of information you use.
- If web results are present, treat them as current/external information, not the \
architect's own vetted notes - flag anything time-sensitive or that should be double-checked.
- Never claim you searched the web or checked external sources unless a "Context from \
web search" section actually appears below - if it's absent, you were not given web results.
- Be precise and technical; this output may be shared externally to demonstrate how a \
vendor meets a stated requirement, so accuracy and clear sourcing matter more than brevity.
"""

# Used by the Live Vendor Test tab, which calls the model directly (no KB/web
# context) to see how a real assistant response fares against the selected
# mock guardrail's response inspection. Deliberately neutral - the RAG
# SYSTEM_PROMPT above assumes a vendor-evaluation framing that would make
# this tab's output nonsensical.
LIVE_TEST_SYSTEM_PROMPT = """You are a plain AI assistant. Answer the user's message directly \
and naturally. You are not aware of any security policy or guardrail - inspection of your \
input and output happens outside of you, before and after this call. Do not refuse based on \
assumed policy; just answer as a normal, helpful assistant would."""
