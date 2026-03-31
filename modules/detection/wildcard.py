import random
import string
from modules.subdomain.resolver import resolve_domain

def detect_wildcard(domain):
    """
    Détecte si un domaine pointe vers une IP par défaut (Wildcard).
    Génère un sous-domaine aléatoire pour tester.
    """
    random_sub = ''.join(random.choices(string.ascii_lowercase, k=12))
    test_domain = f"{random_sub}.{domain}"

    ips = resolve_domain(test_domain)

    if ips:
        # Si un domaine aléatoire répond, le wildcard est actif
        return True, ips
    return False, []