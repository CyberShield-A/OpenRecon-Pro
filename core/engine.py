# core/engine.py
from modules.subdomain.deep_scan import deep_subdomain_scan
from modules.detection.waf_cdn import detect_cdn_waf
from modules.detection.wildcard import detect_wildcard
from utils.logger import banner, success, warning

def run(target, mode="NORMAL", live_output=False):
    banner()
    # Structure de réponse attendue par gui.py
    results = {
        "subdomains": [], # Liste de dictionnaires
        "cdn_waf": "Aucun",
        "wildcard": "Désactivé"
    }
    
    try:
        success(f"[ENGINE] Lancement de l'audit profond sur : {target}")
        
        # 1. Exécution du scan de sous-domaines
        # deep_subdomain_scan retourne un dict avec une clé 'results'
        scan_data = deep_subdomain_scan(target=target, mode=mode, live_output=live_output)
        
        # Extraction de la liste [{'subdomain': '...', 'ips': [...]}, ...]
        results["subdomains"] = scan_data.get("results", [])

        # 2. Détection WAF/CDN
        detection = detect_cdn_waf(target)
        results["cdn_waf"] = detection.get("waf") or detection.get("cdn") or "Aucun"

        # 3. Vérification Wildcard/Joker
        w_status, _ = detect_wildcard(target)
        results["wildcard"] = "Activé" if w_status else "Désactivé"

        success(f"[ENGINE] Scan terminé. {len(results['subdomains'])} cibles trouvées.")

    except Exception as e:
        warning(f"[ENGINE ERROR] Erreur lors de l'exécution : {str(e)}")
    
    return results