"""
Tools for searching the web and scraping content.
"""

import json
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


def search_duckduckgo(query: str) -> str:
    """
    Searches the open web for a given query to find relevant URLs.
    
    Args:
        query: The specific topic or question to research.
        
    Returns:
        A JSON string containing the title, URL, and a brief snippet of the top results.
    """
    try:
        # Fetch top 3 results to keep context windows manageable
        results = DDGS().text(query, max_results=3)
        return json.dumps(list(results))
    except Exception as e:
        return f"Search failed: {str(e)}"


def scrape_website(url: str) -> str:
    """
    Scrapes a webpage and intelligently extracts the core textual content, 
    ignoring navigation menus, footers, and scripts.
    
    Args:
        url: The exact URL to scrape.
        
    Returns:
        The cleaned, extracted raw text from the webpage.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Strip out noisy HTML elements
        for element in soup(
            ["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Target content-heavy tags
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])
        extracted_text = " ".join(
            [elem.get_text(strip=True) for elem in text_elements])

        # Truncate to the first 5000 characters to prevent LLM context overflow
        return extracted_text[:5000]
    except Exception as e:
        return f"Scraping failed for {url}: {str(e)}"
