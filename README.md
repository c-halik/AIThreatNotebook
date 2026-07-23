# AI Threat Notebook

A Streamlit chatbot for querying an AI security / agentic AI security
knowledge base, with an editable notebook you can add to over time. Runs
fully locally on open-source tooling:

- **UI**: Streamlit
- **LLM**: Ollama (`llama3:8b` by default)
- **Embeddings**: Ollama (`nomic-embed-text`)
- **Vector store**: Chroma (embedded, persisted to `.chroma/`)
- **Orchestration**: LangChain
- **Web search fallback**: DuckDuckGo (via `ddgs`, no API key required), restricted to trusted security sites

See [ARCHITECTURE.md](ARCHITECTURE.md) for a diagram and full artifact reference.
See [DEPLOYMENT.md](DEPLOYMENT.md) for how this gets built and deployed via GitHub Actions.

## Setup

### Option A: Docker Compose (recommended, matches production)

```bash
cd security-chatbot
docker compose up -d --build
docker compose exec app python ingest.py   # build the initial index
```

This runs the app, Ollama, and a one-shot job that pulls `llama3:8b` and
`nomic-embed-text` into a persisted volume. Open http://localhost:8501.
Requires Docker with **at least 8GB of memory** allocated to it (Docker
Desktop's default 4GB will get the model OOM-killed) - see "Resource notes"
in [DEPLOYMENT.md](DEPLOYMENT.md).

### Option B: Local Python venv

```bash
cd security-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Make sure Ollama is running and has the models pulled:

```bash
ollama pull llama3:8b
ollama pull nomic-embed-text
```

Build the initial index from the starter knowledge base:

```bash
python ingest.py
```

Run the app:

```bash
streamlit run app.py
```

## Adding your own knowledge

- **Notebook** (`knowledge_base/notebook/`): your own notes, one markdown
  file per topic. Editable directly in the app's "Knowledge Base / Notebook"
  tab, or by adding `.md` files to that folder yourself.
- **Reference docs** (`knowledge_base/docs/`): longer reference material —
  PDFs or markdown. Upload through the app or drop files in directly.

After adding or editing anything, click **Rebuild index** in the app (or run
`python ingest.py`) to make the changes searchable. The index is rebuilt
from scratch each time, so edits and deletions in the knowledge base are
reflected immediately.

## Web search fallback

If the knowledge base has no strong match for a question (or you force it via
the sidebar), the app searches DuckDuckGo restricted to a curated list of
security sites (Dark Reading, The Hacker News, BleepingComputer,
KrebsOnSecurity, SecurityWeek, OWASP, MITRE ATT&CK/ATLAS) and feeds the
results into the model as clearly-labeled, separate context from your
knowledge base. Answers cite web sources by title + link in the "Sources"
expander so you can tell KB-grounded content from live web content at a
glance.

- Toggle it off entirely, or force it on for every question, from the sidebar.
- Edit `TRUSTED_SECURITY_SITES` in `config.py` to change which sites are searched.
- Tune `KB_RELEVANCE_THRESHOLD` in `config.py` to control how strong a KB
  match must be before the app skips the web search. A small knowledge base
  won't separate "on topic" from "actually answers this" well by embedding
  similarity alone - print `best_score` from `rag/retrieval.py` while testing
  to calibrate this for your own content as it grows.
- Questions containing words like "latest", "recent", "zero-day", etc.
  (see `TIME_SENSITIVE_KEYWORDS` in `config.py`) always trigger a web search,
  since a static knowledge base can never answer "what just happened."
- Requires outbound internet access from wherever the app runs; if you're
  deploying into an isolated cloud lab network, this feature needs an
  egress path to the internet (or should be disabled).

## Swapping models

Edit `config.py`:
- `LLM_MODEL` — any chat model available in `ollama list`
- `EMBED_MODEL` — any embedding model available in `ollama list`

To use a hosted API model instead of Ollama later, swap `ChatOllama` in
`rag/llm.py` for the equivalent LangChain chat model class (e.g.
`ChatAnthropic`, `ChatOpenAI`) — the rest of the app is unaffected.

## Roadmap toward a cloud lab deployment

1. ~~Containerize with Docker~~ - done, see `docker-compose.yml` and
   [DEPLOYMENT.md](DEPLOYMENT.md) for the GitHub Actions build/push/deploy flow.
2. Swap Chroma's local persistence for a client-server vector DB (e.g.
   Qdrant) if multiple people/services need to share the knowledge base.
3. Add authentication (e.g. an OIDC provider like Authentik/Keycloak) in
   front of the Streamlit app before exposing it beyond localhost.
4. Add structured logging/audit trail of queries and retrieved sources for
   compliance in an enterprise lab setting.
