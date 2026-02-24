import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def extract_emails(html):
    """
    Extrait les emails classiques et obfusqués.
    """
    if not html:
        return []

    emails = set()

    patterns = [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}',             # classique
        r'([a-zA-Z0-9._%+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+\.[a-z]{2,})',
        r'([a-zA-Z0-9._%+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+\.[a-z]{2,})',
        r'([a-zA-Z0-9._%+-]+)\s*(?:&#64;)\s*([a-zA-Z0-9.-]+\.[a-z]{2,})',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.I)
        for m in matches:
            if isinstance(m, tuple):
                emails.add(f"{m[0]}@{m[1]}")
            else:
                emails.add(m)
    return list(emails)

def crawl_and_extract_emails(base_url, max_pages=50, live_output=True):
    """
    Crawl complet du site pour récupérer les emails.
    """
    visited = set()
    to_visit = [base_url]
    all_emails = set()
    pages_crawled = 0

    while to_visit and pages_crawled < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            html = r.text
            emails = extract_emails(html)
            all_emails.update(emails)
            if live_output and emails:
                print(f"[EMAILS FOUND] {emails} in {url}")
            soup = BeautifulSoup(html, "html.parser")
            # Extraire liens internes
            for link in soup.find_all("a", href=True):
                full_link = urljoin(base_url, link["href"])
                if urlparse(full_link).netloc == urlparse(base_url).netloc:
                    to_visit.append(full_link)
            pages_crawled += 1
        except requests.RequestException:
            continue
    return list(all_emails)