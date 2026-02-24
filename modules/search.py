import requests
from bs4 import BeautifulSoup
import logging
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

def search_b(query, limit=10):
    results = []
    try:
        url = f"https://www.bing.com/search?q={query}"
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            logging.warning("Search engine returned non-200 status.")
            return results

        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            link = a["href"]
            if link.startswith("http"):
                results.append(link)

        return list(set(results))[:limit]

    except requests.RequestException as e:
        logging.error(f"Search error: {e}")
        return results


def extract_links(html):
    return list(set(re.findall(r'href=["\'](.*?)["\']', html)))