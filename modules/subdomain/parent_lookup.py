# modules/subdomain/parent_lookup.py
"""
Retrouve le domaine parent depuis un sous-domaine donné.

Exemples :
  mail.google.com        → google.com
  api.v2.staging.acme.io → acme.io
  shop.example.co.uk     → example.co.uk

Stratégie :
  1. Extraction structurelle via la liste publique des suffixes (Public Suffix List).
     Si tldextract n'est pas disponible, on utilise un fallback heuristique.
  2. Vérification DNS : le domaine parent résout-il réellement ?
  3. Lookup RDAP optionnel pour enrichir les informations.
"""
import logging
from utils.logger import loading, info, warning

logger = logging.getLogger(__name__)

try:
    import dns.resolver as _dns_resolver
    _HAS_DNS = True
except ImportError:
    _dns_resolver = None
    _HAS_DNS = False


# ─── Extraction du domaine parent ────────────────────────────────────────────

def _extract_with_tldextract(fqdn: str) -> str | None:
    """Utilise tldextract pour extraire le domaine registrable."""
    try:
        import tldextract
        ext = tldextract.extract(fqdn)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
    except ImportError:
        pass
    return None


def _extract_heuristic(fqdn: str) -> str:
    """
    Fallback heuristique : retire les niveaux de sous-domaines un par un
    et teste via DNS jusqu'à trouver un domaine qui résout.

    Pour les TLD composés connus (co.uk, com.br, etc.), retire 3 niveaux max.
    """
    parts = fqdn.rstrip(".").split(".")

    # TLD composés courants (2 parties dans le TLD)
    compound_tlds = {
        "co.uk", "co.nz", "co.za", "com.au", "com.br", "com.ar",
        "org.uk", "net.uk", "gov.uk", "edu.au", "ac.uk", "ac.nz",
        "com.mx", "com.co", "net.au", "org.au",
    }

    # Détecter si le TLD est composé
    potential_tld = ".".join(parts[-2:]) if len(parts) >= 2 else ""
    tld_parts = 2 if potential_tld in compound_tlds else 1

    # Le domaine parent minimal = 1 niveau avant le TLD
    min_parts = tld_parts + 1
    if len(parts) <= min_parts:
        return fqdn  # Déjà un domaine racine

    return ".".join(parts[-min_parts:])


def _dns_resolves(domain: str) -> bool:
    """Vérifie si un domaine résout via DNS (NS ou A record)."""
    if not _HAS_DNS:
        return False
    for rtype in ("NS", "A", "SOA"):
        try:
            _dns_resolver.resolve(domain, rtype, lifetime=5)
            return True
        except Exception:
            continue
    return False


def find_parent_domain(subdomain: str) -> dict:
    """
    Retrouve le domaine parent depuis un sous-domaine.

    Args:
        subdomain: FQDN quelconque, ex: "api.v2.staging.example.com"

    Returns:
        dict avec les clés :
          - subdomain      : entrée normalisée
          - parent_domain  : domaine parent trouvé
          - method         : méthode utilisée ('tldextract' | 'heuristic' | 'dns_walk')
          - dns_verified   : bool — le parent résout-il en DNS ?
          - levels_removed : nombre de sous-domaines retirés
          - parts          : liste des composantes du sous-domaine
    """
    subdomain = subdomain.lower().strip().rstrip(".")
    parts = subdomain.split(".")

    result = {
        "subdomain": subdomain,
        "parent_domain": None,
        "method": None,
        "dns_verified": False,
        "levels_removed": 0,
        "parts": parts,
    }

    if len(parts) < 2:
        warning(f"[PARENT] '{subdomain}' n'est pas un FQDN valide.")
        result["parent_domain"] = subdomain
        return result

    # 1. Tentative avec tldextract (le plus précis)
    loading(f"[PARENT] Recherche du domaine parent pour : {subdomain}")
    parent = _extract_with_tldextract(subdomain)
    if parent and parent != subdomain:
        result["parent_domain"] = parent
        result["method"] = "tldextract"
        result["levels_removed"] = len(parts) - len(parent.split("."))
    else:
        # 2. Fallback heuristique
        parent = _extract_heuristic(subdomain)
        result["parent_domain"] = parent
        result["method"] = "heuristic"
        result["levels_removed"] = len(parts) - len(parent.split("."))

    # 3. Vérification DNS du domaine parent
    info(f"[PARENT] Vérification DNS pour : {result['parent_domain']}")
    result["dns_verified"] = _dns_resolves(result["parent_domain"])

    # 4. Si le parent heuristique ne résout pas, remonter niveau par niveau
    if not result["dns_verified"] and result["method"] == "heuristic":
        min_depth = len(result["parent_domain"].split("."))
        for depth in range(len(parts) - 1, min_depth - 1, -1):
            candidate = ".".join(parts[-depth:]) if depth <= len(parts) else subdomain
            if _dns_resolves(candidate):
                result["parent_domain"] = candidate
                result["method"] = "dns_walk"
                result["levels_removed"] = len(parts) - depth
                result["dns_verified"] = True
                break

    info(
        f"[PARENT] {subdomain} → {result['parent_domain']} "
        f"(méthode: {result['method']}, DNS vérifié: {result['dns_verified']})"
    )
    return result
