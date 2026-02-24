from utils.logger import section, info, critical, summary
from modules.email import crawl_and_extract_emails
from modules.search import extract_links
from modules.contact import extract_phones, extract_ips, classify_ip, classify_phone
import socket
from urllib.parse import urlparse

def get_domain_ip(url):
    """
    Récupère l'IP principale du domaine
    """
    domain = urlparse(url).netloc
    try:
        return socket.gethostbyname(domain)
    except:
        return None

def run(target, html=None, base_url=None, live_output=True, max_pages=50):
    links = extract_links(html) if html else []
    emails = crawl_and_extract_emails(base_url, max_pages=max_pages, live_output=live_output)
    phones = extract_phones(html) if html else []
    ips = extract_ips(html) if html else []

    # Ajouter IP du domaine
    domain_ip = get_domain_ip(base_url)
    if domain_ip:
        ips.append(domain_ip)

    results = {"links": links, "emails": [], "phones": [], "ips": []}

    section("LINKS")
    for link in links:
        info(link)

    section("EMAILS")
    for email in emails:
        level = "critical" if target in email else "info"
        (critical if level=="critical" else info)(email)
        results["emails"].append({"value": email, "level": level})

    section("PHONES")
    for phone in phones:
        level = classify_phone(phone)
        (critical if level=="critical" else info)(phone)
        results["phones"].append({"value": phone, "level": level})

    section("IP ADDRESSES")
    for ip in ips:
        level = classify_ip(ip)
        (critical if level=="critical" else info)(ip)
        results["ips"].append({"value": ip, "level": level})

    summary(results)
    return results