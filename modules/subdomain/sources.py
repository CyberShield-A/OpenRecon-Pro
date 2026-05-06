import requests
import logging
from utils.logger import loading

logger = logging.getLogger(__name__)

# Wordlist étendue : préfixes les plus courants (SecLists-inspired)
COMMON_WORDLIST = [
    # Basiques
    "www", "www2", "www3", "mail", "email", "webmail", "smtp", "imap", "pop", "pop3",
    # Dev / CI
    "dev", "dev2", "develop", "development", "staging", "stage", "stg",
    "beta", "alpha", "preview", "demo", "sandbox", "test", "testing", "qa",
    # Infra
    "api", "api2", "api-v1", "api-v2", "rest", "graphql", "gateway",
    "admin", "administrator", "panel", "dashboard", "backoffice", "back",
    "portal", "intranet", "internal", "private", "secure", "shop", "store",
    # Réseau
    "vpn", "ssh", "ftp", "sftp", "ns", "ns1", "ns2", "dns", "mx",
    # Cloud / CDN
    "cdn", "cdn1", "assets", "static", "media", "img", "images", "upload",
    "s3", "storage", "files", "download",
    # App
    "app", "app2", "mobile", "m", "webapp", "web",
    # Prod
    "prod", "production", "live", "cloud", "status", "monitor", "health",
    # Auth / SSO
    "auth", "sso", "login", "oauth", "id", "accounts",
]


def _parse_subdomains(raw_set, domain):
    """Filtre et normalise une collection de noms vers des sous-domaines valides."""
    results = set()
    for name in raw_set:
        name = name.strip().lower().replace("*.", "")
        if name and domain in name and name != domain:
            results.add(name)
    return results


def from_crtsh(domain):
    """Récupère les sous-domaines via les certificats SSL (crt.sh)."""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    results = set()
    loading(f"Interrogation de crt.sh pour {domain}...")

    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            logger.warning(f"crt.sh a répondu avec HTTP {r.status_code} pour {domain}")
            return results
        try:
            data = r.json()
        except ValueError as e:
            logger.error(f"Erreur parsing JSON crt.sh pour {domain}: {e}")
            return results

        raw = set()
        for entry in data:
            for sub in entry.get("name_value", "").split("\n"):
                raw.add(sub)
        return _parse_subdomains(raw, domain)

    except requests.RequestException as e:
        logger.warning(f"Erreur réseau crt.sh pour {domain}: {e}")
    except Exception:
        logger.exception(f"Erreur inattendue dans from_crtsh({domain})")

    return results


def from_hackertarget(domain):
    """Récupère les sous-domaines via HackerTarget (gratuit, sans clé API)."""
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    results = set()
    loading(f"Interrogation de HackerTarget pour {domain}...")

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            logger.warning(f"HackerTarget HTTP {r.status_code} pour {domain}")
            return results

        text = r.text.strip()
        # Réponse = "subdomain.example.com,1.2.3.4" par ligne
        if "error" in text.lower() or "API count" in text:
            logger.warning(f"HackerTarget limite atteinte pour {domain}: {text[:80]}")
            return results

        raw = {line.split(",")[0] for line in text.splitlines() if "," in line}
        return _parse_subdomains(raw, domain)

    except requests.RequestException as e:
        logger.warning(f"Erreur réseau HackerTarget pour {domain}: {e}")
    except Exception:
        logger.exception(f"Erreur inattendue dans from_hackertarget({domain})")

    return results


def from_alienvault(domain):
    """Récupère les sous-domaines via AlienVault OTX (gratuit, sans clé API)."""
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
    results = set()
    loading(f"Interrogation de AlienVault OTX pour {domain}...")

    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "OpenRecon-Pro/2.0"})
        if r.status_code != 200:
            logger.warning(f"AlienVault OTX HTTP {r.status_code} pour {domain}")
            return results

        data = r.json()
        raw = {entry.get("hostname", "") for entry in data.get("passive_dns", [])}
        return _parse_subdomains(raw, domain)

    except requests.RequestException as e:
        logger.warning(f"Erreur réseau AlienVault pour {domain}: {e}")
    except Exception:
        logger.exception(f"Erreur inattendue dans from_alienvault({domain})")

    return results


def from_bruteforce(domain):
    """Génère les candidats brute-force depuis la wordlist étendue."""
    return {f"{w}.{domain}" for w in COMMON_WORDLIST}