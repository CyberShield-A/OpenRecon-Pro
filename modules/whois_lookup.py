# modules/whois_lookup.py
import requests
from utils.logger import loading, info, warning

# Serveurs RDAP bootstrap par TLD
RDAP_BOOTSTRAP_URL = "https://rdap.org/domain/"

def lookup_whois(domain):
    """
    Récupère les informations d'enregistrement d'un domaine via RDAP (HTTP/JSON).
    RDAP est le remplaçant moderne de WHOIS — utilise HTTPS, jamais bloqué par les routeurs.
    Retourne un dictionnaire avec les données clés.
    """
    loading(f"Interrogation RDAP pour {domain}...")
    result = {
        "registrar": None,
        "creation_date": None,
        "expiration_date": None,
        "name_servers": [],
        "registrant": None,
        "emails": [],
        "dnssec": None,
        "privacy": False
    }

    try:
        r = requests.get(
            f"{RDAP_BOOTSTRAP_URL}{domain}",
            timeout=15,
            headers={"Accept": "application/rdap+json"}
        )
        if r.status_code != 200:
            warning(f"RDAP a retourné le code {r.status_code} pour {domain}")
            return result

        data = r.json()

        # Registrar — chercher l'entité avec le rôle "registrar"
        for entity in data.get("entities", []):
            roles = entity.get("roles", [])
            if "registrar" in roles:
                # Nom du registrar
                vcard = _extract_vcard(entity)
                result["registrar"] = vcard.get("fn") or entity.get("handle")

            # Registrant / contact administratif
            if "registrant" in roles:
                vcard = _extract_vcard(entity)
                result["registrant"] = vcard.get("fn") or vcard.get("org")
                if vcard.get("email"):
                    result["emails"].append(vcard["email"])

            # Sous-entités (registrar qui contient le registrant)
            for sub_entity in entity.get("entities", []):
                sub_roles = sub_entity.get("roles", [])
                if "registrant" in sub_roles or "administrative" in sub_roles:
                    vcard = _extract_vcard(sub_entity)
                    if not result["registrant"]:
                        result["registrant"] = vcard.get("fn") or vcard.get("org")
                    if vcard.get("email") and vcard["email"] not in result["emails"]:
                        result["emails"].append(vcard["email"])

        # Dates d'événements
        for event in data.get("events", []):
            action = event.get("eventAction", "")
            date = event.get("eventDate", "")
            if action == "registration":
                result["creation_date"] = date[:10]  # YYYY-MM-DD
            elif action == "expiration":
                result["expiration_date"] = date[:10]

        # Name servers
        ns_list = data.get("nameservers", [])
        result["name_servers"] = [
            ns.get("ldhName", "").lower() for ns in ns_list if ns.get("ldhName")
        ]

        # DNSSEC
        secure_dns = data.get("secureDNS", {})
        if secure_dns.get("delegationSigned"):
            result["dnssec"] = "signed"
        else:
            result["dnssec"] = "unsigned"

        # Détection de la protection vie privée
        privacy_keywords = ["privacy", "proxy", "redacted", "whoisguard", "protection", "domains by proxy", "withheld"]
        registrant_str = str(result["registrant"] or "").lower()
        if any(kw in registrant_str for kw in privacy_keywords) or not result["registrant"]:
            result["privacy"] = True
            if not result["registrant"]:
                result["registrant"] = "Non disponible (protégé ou masqué)"

        info(f"RDAP : registrar={result['registrar']}, expiration={result['expiration_date']}")

    except requests.RequestException as e:
        warning(f"Impossible de contacter le serveur RDAP : {e}")
    except (KeyError, ValueError) as e:
        warning(f"Erreur lors du parsing RDAP : {e}")

    return result


def _extract_vcard(entity):
    """Extrait les infos utiles d'une vCard jCard (format RDAP)."""
    vcard_data = {"fn": None, "org": None, "email": None}

    vcard_array = entity.get("vcardArray", [])
    if len(vcard_array) < 2:
        return vcard_data

    for field in vcard_array[1]:
        if len(field) < 4:
            continue
        field_name = field[0]
        field_value = field[3]
        if field_name == "fn":
            vcard_data["fn"] = field_value
        elif field_name == "org":
            vcard_data["org"] = field_value if isinstance(field_value, str) else str(field_value)
        elif field_name == "email":
            vcard_data["email"] = field_value

    return vcard_data
