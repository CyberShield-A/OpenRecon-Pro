# modules/detection/headers.py
import re
import secrets
import requests
from utils.logger import loading, info, warning

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

# ── Définition des en-têtes avec poids et validation de valeur ───────────────
# "weight"   : contribution au score (total des poids = 100)
# "validate" : fonction(valeur) → (bool ok, str|None avertissement)
#              Si validate est None, seule la présence est vérifiée.

def _validate_hsts(val: str):
    m = re.search(r'max-age=(\d+)', val, re.IGNORECASE)
    if not m:
        return False, "max-age manquant"
    age = int(m.group(1))
    if age < 31536000:
        return True, f"max-age={age} recommandé ≥ 31536000 (1 an)"
    if 'includeSubDomains' not in val:
        return True, "includeSubDomains absent — sous-domaines non protégés"
    return True, None

def _validate_csp(val: str):
    if val.strip() in ("", "*"):
        return False, "Valeur vide ou trop permissive"
    if "unsafe-inline" in val and "unsafe-eval" in val:
        return True, "unsafe-inline + unsafe-eval présents — protection XSS réduite"
    if "unsafe-inline" in val:
        return True, "unsafe-inline présent — protection XSS partielle"
    return True, None

def _validate_xfo(val: str):
    if val.upper() not in ("DENY", "SAMEORIGIN"):
        return False, f"Valeur invalide : '{val}' (attendu DENY ou SAMEORIGIN)"
    return True, None

def _validate_xcto(val: str):
    if val.lower() != "nosniff":
        return False, f"Valeur invalide : '{val}' (attendu nosniff)"
    return True, None

def _validate_referrer(val: str):
    safe = {"no-referrer", "no-referrer-when-downgrade", "strict-origin",
            "strict-origin-when-cross-origin", "same-origin"}
    if val.lower() not in safe:
        return True, f"Valeur '{val}' peut exposer des URLs — préférer strict-origin"
    return True, None

def _validate_xxss(val: str):
    # Cet en-tête est obsolète — noter même s'il est présent
    if val.strip() == "0":
        return True, "Valeur 0 désactive la protection (intentionnel si CSP présent)"
    return True, None

SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "Force l'utilisation de HTTPS",
        "risk": "Élevé",
        "impact": "Sans cet en-tête, MITM et downgrade HTTPS sont possibles.",
        "weight": 25,
        "validate": _validate_hsts,
    },
    "Content-Security-Policy": {
        "description": "Contrôle les ressources chargées par le navigateur",
        "risk": "Élevé",
        "impact": "Absence = vulnérabilité XSS permettant le vol de données.",
        "weight": 25,
        "validate": _validate_csp,
    },
    "X-Frame-Options": {
        "description": "Bloque l'intégration dans un iframe",
        "risk": "Moyen",
        "impact": "Clickjacking possible sans cet en-tête.",
        "weight": 15,
        "validate": _validate_xfo,
    },
    "X-Content-Type-Options": {
        "description": "Empêche le MIME sniffing",
        "risk": "Moyen",
        "impact": "Un fichier malveillant pourrait être interprété comme du code.",
        "weight": 15,
        "validate": _validate_xcto,
    },
    "Referrer-Policy": {
        "description": "Contrôle les informations envoyées à d'autres sites",
        "risk": "Faible",
        "impact": "Des URLs sensibles peuvent fuiter vers des tiers.",
        "weight": 10,
        "validate": _validate_referrer,
    },
    "Permissions-Policy": {
        "description": "Restreint l'accès aux API du navigateur (caméra, micro…)",
        "risk": "Faible",
        "impact": "Des scripts tiers peuvent accéder à des capteurs sensibles.",
        "weight": 8,
        "validate": None,
    },
    "X-XSS-Protection": {
        "description": "Protection XSS des anciens navigateurs (obsolète)",
        "risk": "Faible",
        "impact": "Couche additionnelle absente (peu critique si CSP est présent).",
        "weight": 2,
        "validate": _validate_xxss,
    },
}

TOTAL_WEIGHT = sum(h["weight"] for h in SECURITY_HEADERS.values())  # = 100


def _get_header_ci(headers, name: str):
    """Retourne (clé_originale, valeur) en ignorant la casse, ou (None, None)."""
    for k, v in headers.items():
        if k.lower() == name.lower():
            return k, v
    return None, None


def scan_security_headers(domain: str) -> dict:
    """
    Audite les en-têtes de sécurité HTTP d'un domaine.

    Retourne :
        present   : { header → { value, warning } }
        missing   : { header → { description, risk, impact, weight } }
        warnings  : [ { header, message } ]   ← valeurs présentes mais mal configurées
        score     : int 0-100  (pondéré par criticité + pénalité si valeur invalide)
        grade     : A / B / C / D / F
        server    : valeur du header Server
        all_headers : dict complet des headers reçus
    """
    loading(f"Analyse des en-têtes de sécurité pour {domain}...")

    result = {
        "present":     {},
        "missing":     {},
        "warnings":    [],
        "score":       0,
        "grade":       "F",
        "server":      None,
        "all_headers": {},
    }

    try:
        r = requests.get(
            f"https://{domain}",
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": secrets.choice(USER_AGENTS)},
        )

        headers = r.headers
        result["all_headers"] = dict(headers)
        result["server"] = headers.get("Server")

        earned = 0

        for header, meta in SECURITY_HEADERS.items():
            _, val = _get_header_ci(headers, header)

            if val is None:
                # En-tête absent
                result["missing"][header] = {
                    "description": meta["description"],
                    "risk":        meta["risk"],
                    "impact":      meta["impact"],
                    "weight":      meta["weight"],
                }
                continue

            # En-tête présent — validation de la valeur
            warn_msg = None
            valid = True
            if meta["validate"]:
                valid, warn_msg = meta["validate"](val)

            result["present"][header] = {
                "value":   val,
                "warning": warn_msg,
            }

            if valid:
                # Plein poids si valeur correcte, moitié si warn non bloquant
                earned += meta["weight"] if warn_msg is None else meta["weight"] * 0.6
            else:
                # Valeur présente mais invalide → compté comme quasi-absent
                earned += meta["weight"] * 0.1
                result["missing"][header] = {
                    "description": meta["description"],
                    "risk":        meta["risk"],
                    "impact":      f"Valeur incorrecte : {warn_msg}",
                    "weight":      meta["weight"],
                }
                del result["present"][header]

            if warn_msg:
                result["warnings"].append({"header": header, "message": warn_msg})

        score = round(earned)
        result["score"] = score
        result["grade"] = (
            "A" if score >= 85 else
            "B" if score >= 70 else
            "C" if score >= 50 else
            "D" if score >= 30 else "F"
        )

        present_count = len(result["present"])
        total_count = len(SECURITY_HEADERS)
        info(f"Headers : {present_count}/{total_count} présents · score {score}/100 · grade {result['grade']}")

    except requests.RequestException as e:
        warning(f"Impossible d'analyser les headers de {domain} : {e}")

    return result
