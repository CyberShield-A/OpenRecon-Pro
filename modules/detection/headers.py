# modules/detection/headers.py
import requests
from utils.logger import loading, info, warning

# En-têtes de sécurité critiques et leur rôle
SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "Force l'utilisation de HTTPS (connexion chiffrée)",
        "risk": "Élevé",
        "impact": "Sans cet en-tête, un attaquant peut intercepter les communications entre l'utilisateur et le site (attaque man-in-the-middle)."
    },
    "Content-Security-Policy": {
        "description": "Contrôle les ressources que le navigateur peut charger",
        "risk": "Élevé",
        "impact": "Sans cet en-tête, le site est vulnérable aux injections de scripts malveillants (XSS) qui peuvent voler des données utilisateurs."
    },
    "X-Frame-Options": {
        "description": "Empêche l'intégration du site dans un cadre (iframe)",
        "risk": "Moyen",
        "impact": "Un attaquant pourrait intégrer le site dans un faux site pour piéger les utilisateurs (clickjacking)."
    },
    "X-Content-Type-Options": {
        "description": "Empêche le navigateur de deviner le type de fichier",
        "risk": "Moyen",
        "impact": "Un fichier malveillant pourrait être interprété comme du code exécutable."
    },
    "Referrer-Policy": {
        "description": "Contrôle les informations envoyées lors de la navigation",
        "risk": "Faible",
        "impact": "Des informations sensibles de l'URL pourraient fuiter vers des sites tiers."
    },
    "Permissions-Policy": {
        "description": "Contrôle l'accès aux fonctionnalités du navigateur (caméra, micro, etc.)",
        "risk": "Faible",
        "impact": "Des scripts tiers pourraient accéder à la caméra, au micro ou à la géolocalisation."
    },
    "X-XSS-Protection": {
        "description": "Protection basique contre les injections de scripts",
        "risk": "Faible",
        "impact": "Couche de protection supplémentaire absente (moins critique si CSP est présent)."
    }
}


def scan_security_headers(domain):
    """
    Vérifie la présence des en-têtes de sécurité HTTP.
    Retourne un dictionnaire avec les headers présents, manquants, et un score.
    """
    loading(f"Analyse des en-têtes de sécurité pour {domain}...")

    result = {
        "present": {},     # header -> valeur
        "missing": {},     # header -> {description, risk, impact}
        "score": 0,        # score sur 100
        "grade": "F",
        "server": None,
        "all_headers": {}
    }

    try:
        r = requests.get(
            f"https://{domain}",
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )

        headers = r.headers
        result["all_headers"] = dict(headers)
        result["server"] = headers.get("Server")

        # Vérification de chaque header de sécurité
        for header, details in SECURITY_HEADERS.items():
            if header.lower() in {k.lower(): k for k in headers}:
                # Trouver la bonne clé (case insensitive)
                actual_key = next(k for k in headers if k.lower() == header.lower())
                result["present"][header] = headers[actual_key]
            else:
                result["missing"][header] = details

        # Calcul du score
        total = len(SECURITY_HEADERS)
        present = len(result["present"])
        result["score"] = round((present / total) * 100)

        # Grade
        score = result["score"]
        if score >= 85:
            result["grade"] = "A"
        elif score >= 70:
            result["grade"] = "B"
        elif score >= 50:
            result["grade"] = "C"
        elif score >= 30:
            result["grade"] = "D"
        else:
            result["grade"] = "F"

        info(f"Headers de sécurité : {present}/{total} présents (score: {result['score']}%, grade: {result['grade']})")

    except requests.RequestException as e:
        warning(f"Impossible d'analyser les headers de {domain} : {e}")

    return result
