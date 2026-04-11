import requests
import logging
from utils.logger import loading

logger = logging.getLogger(__name__)

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

        if r.status_code != 200:
            logger.warning(f"crt.sh a répondu avec un code HTTP {r.status_code} pour {domain}")
            return results

        try:
            data = r.json()
        except ValueError as e:
            logger.error(f"Erreur parsing JSON crt.sh pour {domain}: {e}")
            return results

        for entry in data:
            name = entry.get("name_value", "").lower()
            for sub in name.split("\n"):
                sub = sub.replace("*.", "").strip()
                if domain in sub and sub != domain:
                    results.add(sub)

    except requests.RequestException as e:
        logger.warning(f"Erreur réseau lors de l'accès à crt.sh pour {domain}: {e}")

    except Exception as e:
        logger.exception(f"Erreur inattendue dans from_crtsh({domain})")

    return results


def from_bruteforce(domain):
    """Génère une liste de candidats pour le brute-force"""
    return {f"{w}.{domain}" for w in COMMON_WORDLIST}