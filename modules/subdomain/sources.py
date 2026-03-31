import requests
from utils.logger import loading

COMMON_WORDLIST = [
    "www", "mail", "dev", "test", "api", "admin", "portal",
    "vpn", "staging", "beta", "secure", "internal", "app", "prod"
]

def from_crtsh(domain):
    """Récupère les sous-domaines via les certificats SSL (crt.sh)"""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    results = set()
    loading(f"Interrogation de crt.sh pour {domain}...")

    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for entry in data:
                name = entry.get("name_value", "").lower()
                for sub in name.split("\n"):
                    # Nettoyage des wildcards et espaces
                    sub = sub.replace("*.", "").strip()
                    if domain in sub and sub != domain:
                        results.add(sub)
    except Exception:
        pass
    return results

def from_bruteforce(domain):
    """Génère une liste de candidats pour le brute-force"""
    return {f"{w}.{domain}" for w in COMMON_WORDLIST}