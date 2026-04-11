import secrets
import string
import re
from modules.subdomain.resolver import resolve_domain

def is_valid_domain(domain):
    return re.match(r"^[a-zA-Z0-9.-]+$", domain) is not None

def generate_random_subdomain(length=12):
    alphabet = string.ascii_lowercase
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def detect_wildcard(domain):
    """
    Détecte si un domaine utilise un wildcard DNS.
    """

    if not is_valid_domain(domain):
        return False, []

    sub1 = generate_random_subdomain()
    sub2 = generate_random_subdomain()

    ips1 = resolve_domain(f"{sub1}.{domain}")
    ips2 = resolve_domain(f"{sub2}.{domain}")

    if ips1 and ips2 and ips1 == ips2:
        return True, ips1

    return False, []