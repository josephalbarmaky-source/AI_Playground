"""Web search tool via DuckDuckGo."""
from __future__ import annotations

import asyncio
from typing import Any


async def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Return a list of search results: {title, href, body}."""
    from duckduckgo_search import DDGS

    def _run() -> list[dict[str, Any]]:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    return await asyncio.to_thread(_run)


def format_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "").strip()
        body = r.get("body", "").strip()
        href = r.get("href", "").strip()
        snippet = body[:160] + ("…" if len(body) > 160 else "")
        lines.append(f"{i}. {title}\n   {snippet}\n   {href}")
    return "\n\n".join(lines)
