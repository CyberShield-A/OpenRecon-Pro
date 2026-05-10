import ipaddress
import socket
import secrets
import requests
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]

# ── CDN : détecté par en-têtes HTTP ──────────────────────────────────────────
# Chaque entrée = (provider_name, [patterns dans les headers])
CDN_HEADER_PATTERNS = {
    "Cloudflare":  ["cf-ray", "cf-cache-status", "cf-request-id"],
    "Akamai":      ["akamai-origin-hop", "x-check-cacheable", "x-akamai-request-id"],
    "Fastly":      ["x-fastly-request-id", "x-served-by", "fastly-"],
    "CloudFront":  ["x-amz-cf-id", "x-amz-cf-pop", "via: cloudfront"],
    "BunnyCDN":    ["bunnycdn", "cdn-pullzone"],
    "KeyCDN":      ["x-edge-location", "x-cache: keycdn"],
    "StackPath":   ["x-sp-url", "x-sp-cache"],
    "Limelight":   ["x-llnw-"],
    "Edgio":       ["x-edgio-"],
    "Azure CDN":   ["x-msedge-ref", "x-azure-ref"],
}

# ── WAF : détecté par en-têtes HTTP ──────────────────────────────────────────
WAF_HEADER_PATTERNS = {
    "Cloudflare WAF":  ["cloudflare", "cf-ray"],
    "Imperva (Incapsula)": ["x-iinfo", "incap-ses", "visid_incap"],
    "Sucuri WAF":      ["x-sucuri-id", "x-sucuri-cache"],
    "F5 BIG-IP":       ["x-wa-info", "x-cnection", "bigipserver"],
    "Barracuda WAF":   ["barra_counter_session", "barracuda_"],
    "Fortinet FortiWeb": ["fortigate", "fortiwebappid"],
    "AWS WAF":         ["x-amzn-requestid", "x-amzn-trace-id"],
    "Nginx WAF (ModSec)": ["x-mod-pagespeed", "x-page-speed"],
    "Akamai WAF":      ["x-akamai-"],
    "Wallarm":         ["x-wallarm-node"],
    "Reblaze":         ["x-reblaze-protection"],
    "DenyAll":         ["x-denyall-"],
    "Wordfence":       ["wfvt_", "wordfence"],
}

# ── CDN : détecté par plages d'IP connues ────────────────────────────────────
# Source : listes officielles et bases publiques (CIDR)
CDN_IP_RANGES: dict[str, list[str]] = {
    "Cloudflare": [
        "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
        "104.16.0.0/13",   "104.24.0.0/14",   "108.162.192.0/18",
        "131.0.72.0/22",   "141.101.64.0/18",  "162.158.0.0/15",
        "172.64.0.0/13",   "173.245.48.0/20",  "188.114.96.0/20",
        "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
    ],
    "Akamai": [
        "23.32.0.0/11", "23.64.0.0/14", "23.192.0.0/11",
        "104.64.0.0/10", "184.24.0.0/13",
    ],
    "Fastly": [
        "23.235.32.0/20", "43.249.72.0/22", "103.244.50.0/24",
        "103.245.222.0/23", "104.156.80.0/20", "151.101.0.0/16",
        "157.52.64.0/18",  "167.82.0.0/17",   "185.31.16.0/22",
        "199.27.72.0/21",
    ],
    "CloudFront": [
        "13.32.0.0/15", "13.35.0.0/16", "52.46.0.0/18",
        "52.84.0.0/15",  "54.182.0.0/16", "54.192.0.0/16",
        "64.252.64.0/18", "70.132.0.0/18",
    ],
    "Azure CDN": [
        "13.107.246.0/24", "13.107.213.0/24",
    ],
}


def _random_ua() -> str:
    return secrets.choice(USER_AGENTS)


def _resolve_ips(domain: str) -> list[str]:
    """Résout le domaine en IPs via socket (IPv4 uniquement)."""
    try:
        infos = socket.getaddrinfo(domain, None, socket.AF_INET)
        return list(dict.fromkeys(i[4][0] for i in infos))
    except socket.gaierror:
        return []


def _match_ip_to_cdn(ips: list[str]) -> str | None:
    """Retourne le nom du CDN si une des IPs tombe dans ses plages connues."""
    for provider, cidrs in CDN_IP_RANGES.items():
        for cidr in cidrs:
            network = ipaddress.ip_network(cidr, strict=False)
            for ip_str in ips:
                try:
                    if ipaddress.ip_address(ip_str) in network:
                        return provider
                except ValueError:
                    continue
    return None


def _match_headers(headers_str: str, patterns: dict[str, list[str]]) -> str | None:
    """Retourne le premier provider dont un pattern est trouvé dans headers_str."""
    h = headers_str.lower()
    for provider, keywords in patterns.items():
        if any(kw in h for kw in keywords):
            return provider
    return None


def detect_cdn_waf(domain: str) -> dict:
    """
    Détecte le CDN et le WAF d'un domaine via trois méthodes combinées :
      1. Résolution DNS + correspondance de plages IP CDN connues
      2. Patterns dans les en-têtes HTTP de la réponse (CDN)
      3. Patterns dans les en-têtes HTTP de la réponse (WAF)

    Retourne : { "cdn": str|None, "waf": str|None, "ips": list[str], "method": str }
    """
    result: dict = {"cdn": None, "waf": None, "ips": [], "method": "none"}

    # 1. Résolution DNS → correspondance IP ranges
    ips = _resolve_ips(domain)
    result["ips"] = ips

    cdn_by_ip = _match_ip_to_cdn(ips)
    if cdn_by_ip:
        result["cdn"] = cdn_by_ip
        result["method"] = "ip_range"

    # 2 & 3. En-têtes HTTP
    try:
        r = requests.get(
            f"http://{domain}",
            timeout=6,
            allow_redirects=True,
            headers={"User-Agent": _random_ua()},
        )
        headers_str = " ".join(f"{k}: {v}" for k, v in r.headers.items())

        cdn_by_header = _match_headers(headers_str, CDN_HEADER_PATTERNS)
        waf_by_header = _match_headers(headers_str, WAF_HEADER_PATTERNS)

        # Le header prend la priorité sur l'IP range si les deux concordent
        if cdn_by_header:
            result["cdn"] = cdn_by_header
            result["method"] = "header" if not cdn_by_ip else "ip_range+header"

        if waf_by_header:
            result["waf"] = waf_by_header

    except requests.RequestException as e:
        logger.debug(f"Requête HTTP échouée pour {domain}: {e}")

    return result