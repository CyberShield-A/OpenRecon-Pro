# modules/detection/tech.py
import secrets
import webtech
from webtech import WebTech
from webtech.utils import Format
from utils.logger import loading, info, warning

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]


def detect_technologies(domain: str) -> dict:
    """
    Identifie les technologies d'un site via webtech (base Wappalyzer ~1800 techs).

    Retourne :
        server       : valeur du header Server (str | None)
        technologies : liste triée des noms détectés
        details      : { nom → version | "Détecté" }
    """
    loading(f"Détection des technologies pour {domain} (webtech)...")

    result: dict = {
        "server":       None,
        "technologies": [],
        "details":      {},
    }

    try:
        wt = WebTech(options={"silent": True})
        wt.output_format = Format["json"]   # doit être défini après instanciation
        wt.USER_AGENT = secrets.choice(USER_AGENTS)

        report = wt.start_from_url(f"https://{domain}", timeout=12)

        # report est un dict JSON quand output_format=json
        if not isinstance(report, dict):
            warning(f"webtech a retourné un format inattendu pour {domain}")
            return result

        detected: dict[str, str] = {}

        for tech in report.get("tech", []):
            name    = tech.get("name", "")
            version = tech.get("version") or None
            if name:
                detected[name] = version if version else "Détecté"

        # Server header (présent dans les custom headers de webtech)
        for header in report.get("headers", []):
            if header.get("name", "").lower() == "server":
                result["server"] = header.get("value")

        result["technologies"] = sorted(detected.keys())
        result["details"]      = detected

        if detected:
            info(f"Technologies ({len(detected)}) : {', '.join(result['technologies'])}")
        else:
            info("Aucune technologie identifiée.")

    except Exception as e:
        warning(f"Erreur webtech pour {domain} : {e}")

    return result

