# modules/subdomain/parent_lookup.py
"""
Retrouve le domaine parent depuis un sous-domaine donné.
"""
import logging
import re
from utils.logger import loading, info, warning

logger = logging.getLogger(__name__)

try:
    import dns.resolver as _dns_resolver
    import dns.exception
    _HAS_DNS = True
except ImportError:
    _dns_resolver = None
    _HAS_DNS = False

# ─── Extraction du domaine parent ────────────────────────────────────────────

def _extract_with_tldextract(fqdn: str) -> str | None:
    """Utilise tldextract pour extraire le domaine registrable."""
    try:
        import tldextract
        # Utilise un cache pour tldextract afin d'accélérer les scans massifs
        ext = tldextract.extract(fqdn)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Erreur tldextract: {e}")
    return None

def _extract_heuristic(fqdn: str) -> str:
    """Fallback heuristique pour les TLD composés."""
    parts = fqdn.rstrip(".").split(".")
    
    compound_tlds = {
        "co.uk", "co.nz", "co.za", "com.au", "com.br", "com.ar",
        "org.uk", "net.uk", "gov.uk", "edu.au", "ac.uk", "ac.nz",
        "com.mx", "com.co", "net.au", "org.au",
    }

    potential_tld = ".".join(parts[-2:]) if len(parts) >= 2 else ""
    tld_parts = 2 if potential_tld in compound_tlds else 1
    min_parts = tld_parts + 1
    
    if len(parts) <= min_parts:
        return fqdn

    return ".".join(parts[-min_parts:])

def _dns_resolves(domain: str) -> bool:
    """Vérifie si un domaine résout via DNS avec gestion propre des exceptions."""
    if not _HAS_DNS or not _dns_resolver:
        return False
        
    # On teste les enregistrements les plus communs pour confirmer l'existence du parent
    for rtype in ("A", "NS", "SOA"):
        try:
            # Lifetime court pour ne pas bloquer le pipeline Jenkins
            _dns_resolver.resolve(domain, rtype, lifetime=2.0)
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # C'est une réponse normale (le domaine n'a pas ce type d'enregistrement)
            continue
        except (dns.resolver.Timeout, dns.exception.Timeout):
            logger.debug(f"Timeout DNS pour {domain} ({rtype})")
            continue
        except Exception as e:
            # Correction Bandit B112 : on log l'erreur inattendue au lieu de juste "continue"
            logger.debug(f"Erreur DNS imprévue sur {domain} : {str(e)}")
            continue
    return False

def find_parent_domain(subdomain: str) -> dict:
    """Retrouve le domaine parent depuis un sous-domaine."""
    # Nettoyage et validation basique
    subdomain = subdomain.lower().strip().rstrip(".")
    if not re.match(r"^[a-z0-9.-]+$", subdomain):
        warning(f"[PARENT] Caractères invalides dans : {subdomain}")
        return {"subdomain": subdomain, "parent_domain": subdomain, "error": "Invalid characters"}

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
        warning(f"[PARENT] '{subdomain}' n'est pas un FQDN complet.")
        result["parent_domain"] = subdomain
        return result

    # 1. Tentative avec tldextract
    loading(f"[PARENT] Analyse de structure : {subdomain}")
    parent = _extract_with_tldextract(subdomain)
    
    if parent and parent != subdomain:
        result["parent_domain"] = parent
        result["method"] = "tldextract"
    else:
        # 2. Fallback heuristique
        parent = _extract_heuristic(subdomain)
        result["parent_domain"] = parent
        result["method"] = "heuristic"

    # Calcul du nombre de niveaux retirés
    result["levels_removed"] = len(parts) - len(result["parent_domain"].split("."))

    # 3. Vérification DNS
    result["dns_verified"] = _dns_resolves(result["parent_domain"])

    # 4. DNS Walk (Si l'heuristique a échoué à trouver un parent résolvable)
    if not result["dns_verified"]:
        # On remonte l'arbre DNS pour trouver le premier parent qui répond
        for i in range(1, len(parts)):
            candidate = ".".join(parts[i:])
            if len(candidate.split(".")) < 2: # Ne pas tester le TLD seul (ex: .com)
                break
            
            if _dns_resolves(candidate):
                result["parent_domain"] = candidate
                result["method"] = "dns_walk"
                result["dns_verified"] = True
                result["levels_removed"] = i
                break

    status = "VÉRIFIÉ" if result["dns_verified"] else "NON VÉRIFIÉ"
    info(f"[PARENT] {subdomain} -> {result['parent_domain']} ({status})")
    
    return result
