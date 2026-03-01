"""
HALO Health – Agentic Search Service
Tries Tavily first (if key is set), falls back to DuckDuckGo.
"""
import logging
from typing import List, Dict

from backend.config import settings

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Returns a list of {title, url, snippet} dicts.
    Tries Tavily → falls back to DuckDuckGo.
    """
    if settings.tavily_api_key:
        try:
            return _tavily_search(query, max_results)
        except Exception as exc:
            logger.warning("Tavily search failed, falling back to DuckDuckGo: %s", exc)

    return _ddg_search(query, max_results)


def _tavily_search(query: str, max_results: int) -> List[Dict[str, str]]:
    from tavily import TavilyClient  # type: ignore

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(query=query, max_results=max_results)
    results = []
    for r in response.get("results", []):
        results.append(
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        )
    return results


def _ddg_search(query: str, max_results: int) -> List[Dict[str, str]]:
    from duckduckgo_search import DDGS  # type: ignore

    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                )
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
    return results


def format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into a readable string for LLM context."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**\n   {r['snippet']}\n   Source: {r['url']}")
    return "\n\n".join(lines)
