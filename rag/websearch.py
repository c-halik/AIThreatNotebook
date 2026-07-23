from ddgs import DDGS
from ddgs.exceptions import DDGSException

import config


def search_security_sources(query: str, max_results: int = config.WEB_MAX_RESULTS):
    """Search trusted security sites via DuckDuckGo. Returns [] on any failure
    (network issue, rate limit) rather than raising, so it never breaks chat."""
    site_filter = " OR ".join(f"site:{site}" for site in config.TRUSTED_SECURITY_SITES)
    full_query = f"{query} ({site_filter})"

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(full_query, max_results=max_results))
    except DDGSException:
        return []

    return [
        {
            "title": r.get("title", "untitled"),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw_results
    ]


def format_web_context(results) -> str:
    if not results:
        return "(no web results found)"
    blocks = []
    for r in results:
        blocks.append(f"[web source: {r['title']} — {r['url']}]\n{r['snippet']}")
    return "\n\n---\n\n".join(blocks)
