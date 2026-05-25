"""
Tools for web searching using DuckDuckGo.
"""

import contextvars

from bs4 import BeautifulSoup
from ddgs import DDGS
import httpx
from loguru import logger

# 1. Define the ContextVar globally.
# Because you are running a web server, this automatically starts at 0
# for every single incoming HTTP request.
search_run_count = contextvars.ContextVar("search_run_count", default=0)
seen_urls_cache = contextvars.ContextVar("seen_urls_cache", default=None)

MAX_SEARCH_RUNS = 1


def fetch_page_text(url: str) -> str:
    """Helper to grab readable text from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = httpx.get(url,
                             headers=headers,
                             timeout=5.0,
                             follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()

        text = soup.get_text(separator="\n", strip=True)
        return text[:4000]
    except Exception as e:
        return f"[Failed to scrape page: {e}]"


def restricted_web_search(query: str,
                          time_limit: str = None,
                          max_results: int = 5) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    Useful for finding up-to-date information, news, and facts.
    :param time_limit: Set to 'd' (day), 'w' (week), 'm' (month), 'y' (year), or None for any time.
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
            search_results = list(
                ddgs.text(query, max_results=max_results, timelimit=time_limit))

            for i, r in enumerate(search_results):
                url = r.get('href')

                # Check the context-isolated URL cache
                if url in current_urls:
                    continue

                current_urls.add(url)

                if i == 0:
                    page_content = fetch_page_text(url)
                    results.append(
                        f"Title: {r.get('title')}\nURL: {url}\nFULL TEXT:\n{page_content}\n"
                    )
                else:
                    results.append(
                        f"Title: {r.get('title')}\nURL: {url}\nSnippet: {r.get('body')}\n"
                    )

        if not results:
            return "No new results found for this query."

        return "\n---\n".join(results)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error performing search: {str(e)}"
