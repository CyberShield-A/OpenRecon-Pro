# core/engine.py
from modules.subdomain.deep_scan import deep_subdomain_scan
from modules.detection.waf_cdn import detect_cdn_waf
from modules.detection.wildcard import detect_wildcard
from modules.detection.headers import scan_security_headers
from modules.detection.tech import detect_technologies
from modules.whois_lookup import lookup_whois
from modules.report import generate_report, save_report, export_html
from utils.logger import banner, success, warning

def run(target, mode="NORMAL", live_output=False, ollama_model=None, report_path=None):
    banner()
    results = {
        "subdomains": [],
        "cdn_waf": "Aucun",
        "wildcard": "Désactivé",
        "whois": {},
        "security_headers": {},
        "technologies": {},
        "report": None
    }

    try:
        success(f"[ENGINE] Lancement de l'audit profond sur : {target}")

        # 1. Scan de sous-domaines
        scan_data = deep_subdomain_scan(target=target, mode=mode, live_output=live_output)
        results["subdomains"] = scan_data.get("results", [])

        # 2. Détection WAF/CDN
        detection = detect_cdn_waf(target)
        results["cdn_waf"] = detection.get("waf") or detection.get("cdn") or "Aucun"

        # 3. Vérification Wildcard
        w_status, _ = detect_wildcard(target)
        results["wildcard"] = "Activé" if w_status else "Désactivé"

        # 4. RDAP (enregistrement du domaine)
        success("[ENGINE] Récupération RDAP...")
        results["whois"] = lookup_whois(target)

        # 5. Audit des en-têtes de sécurité HTTP
        success("[ENGINE] Audit des en-têtes de sécurité...")
        results["security_headers"] = scan_security_headers(target)

        # 6. Détection des technologies
        success("[ENGINE] Détection des technologies...")
        results["technologies"] = detect_technologies(target)

        success(f"[ENGINE] Scan terminé. {len(results['subdomains'])} cibles trouvées.")

        # 7. Génération du rapport IA (optionnel)
        if report_path is not None:
            report_text = generate_report(target, results, model=ollama_model)
            if report_text:
                results["report"] = report_text
                save_report(report_text, report_path)
                html_path = report_path.replace(".txt", ".html") if report_path.endswith(".txt") else report_path + ".html"
                export_html(report_text, target, html_path)

    except Exception as e:
        warning(f"[ENGINE ERROR] Erreur lors de l'exécution : {str(e)}")

    return results