import re
from ipaddress import ip_address, IPv4Address

# 🔹 Extraction des téléphones
def extract_phones(html):
    """
    Extrait tous les numéros de téléphone depuis le HTML.
    Supporte + indicatif, espaces, tirets, parenthèses.
    """
    if not html:
        return []

    phone_pattern = r'\+?\d[\d\s\-\(\)]{7,}\d'  # ex: +212 715-56350, (715) 563 50
    matches = re.findall(phone_pattern, html)
    phones = set()
    for m in matches:
        cleaned = re.sub(r'[\s\-\(\)]', '', m)
        phones.add(cleaned)
    return list(phones)

# 🔹 Extraction des IPs
def extract_ips(html):
    """
    Extrait toutes les adresses IPv4 valides depuis le HTML.
    """
    if not html:
        return []

    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    matches = re.findall(ip_pattern, html)
    ips = set()
    for ip in matches:
        try:
            ip_obj = ip_address(ip)
            if isinstance(ip_obj, IPv4Address):
                ips.add(str(ip_obj))
        except ValueError:
            continue
    return list(ips)

# 🔹 Classification
def classify_ip(ip):
    """
    Classe une IP : privée/loopback = info, publique = critical
    """
    try:
        ip_obj = ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            return "info"
        return "critical"
    except ValueError:
        return "info"

def classify_phone(phone):
    """
    Classe un téléphone : indicatif international autre que +1 ou long numéro = critical
    """
    if phone.startswith("+1") or len(phone) <= 8:
        return "info"
    return "critical"