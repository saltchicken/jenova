"""
Tools for web searching using DuckDuckGo.
"""

import contextvars
from ddgs import DDGS
from loguru import logger

request_run_count = contextvars.ContextVar("search_run_count", default=0)

class WebSearchTool:
    """
    A stateful web search tool that limits how many times it can be executed.
    """
    def __init__(self, max_runs: int = 1):
        self.max_runs = max_runs
        self.__name__ = "restricted_web_search"
        self.__doc__ = self.__call__.__doc__

    def __call__(self, query: str, max_results: int = 5) -> str:
        """
        Performs a web search using DuckDuckGo and returns the results.
        Useful for finding up-to-date information, news, and facts.
        """
        current_count = request_run_count.get()

        if current_count >= self.max_runs:
            logger.warning(f"Web search blocked: Max runs ({self.max_runs}) reached.")
            return "SYSTEM ALARM: You have reached the maximum allowed web searches. Do not call this tool again. Synthesize an answer using the results you already gathered."

        request_run_count.set(current_count + 1)

        logger.info(f"Performing web search for: '{query}' (Run {current_count + 1}/{self.max_runs})")
        
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n")
            
            if not results:
                return "No results found."
            
            return "\n---\n".join(results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Error performing search: {str(e)}"
