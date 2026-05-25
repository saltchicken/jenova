"""
Tools for web searching using DuckDuckGo.
"""

import contextvars

from ddgs import DDGS
from loguru import logger

# 1. Define the ContextVar globally.
# Because you are running a web server, this automatically starts at 0
# for every single incoming HTTP request.
search_run_count = contextvars.ContextVar("search_run_count", default=0)
seen_urls_cache = contextvars.ContextVar("seen_urls_cache", default=None)

MAX_SEARCH_RUNS = 1


def restricted_web_search(query: str, max_results: int = 5) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    Useful for finding up-to-date information, news, and facts.
    """
    current_count = search_run_count.get()
    current_urls = seen_urls_cache.get()

    # If the set is empty, it might be the global default. Let's ensure it's a new instance.
    if not current_urls:
        current_urls = set()
        seen_urls_cache.set(current_urls)

    if current_count >= MAX_SEARCH_RUNS:
        logger.warning(
            f"Web search blocked: Max runs ({MAX_SEARCH_RUNS}) reached.")
        return "SYSTEM ALARM: You have reached the maximum allowed web searches. Synthesize an answer using the results you already gathered."

    # Update the execution count
    search_run_count.set(current_count + 1)
    logger.info(
        f"Performing web search for: '{query}' (Run {current_count + 1}/{MAX_SEARCH_RUNS})"
    )

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                url = r.get('href')

                # Check the context-isolated URL cache
                if url in current_urls:
                    continue

                current_urls.add(url)
                results.append(
                    f"Title: {r.get('title')}\nURL: {url}\nSnippet: {r.get('body')}\n"
                )

        if not results:
            return "No new results found for this query."

        return "\n---\n".join(results)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error performing search: {str(e)}"
