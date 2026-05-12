# core/engine.py
import logging
from modules.subdomain.scanner import Subscanner
from modules.recon.webtech_wrapper import TechScanner
from modules.recon.headers import HeaderAnalyzer
from modules.recon.whois_lookup import WhoisLookup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenRecon-Engine")

def run(target):
    logger.info(f"🚀 Lancement du scan complet sur : {target}")
    
    # Structure de données complète pour gui.py
    results = {
        "target": target,
        "subdomains": [], # Contiendra Nom + IPs + Confidence (Brute Force)
        "technologies": {"technologies": []},
        "security_headers": {"score": 0, "grade": "N/A", "present": [], "missing": {}},
        "whois": {},
        "cdn_waf": "Analyse en cours...",
        "wildcard": "Non"
    }

    try:
        # 1. BRUTE FORCE & ÉNUMÉRATION (Sous-domaines + IPs)
        logger.info("📡 Phase 1 : Énumération et Brute Force des IPs...")
        scanner = Subscanner(target)
        # C'est ici que tu récupères la liste des dictionnaires {'subdomain':..., 'ips': [...]}
        results["subdomains"] = scanner.enumerate() 
        
        # 2. IDENTIFICATION DES TECHNOLOGIES
        # On cible le domaine principal pour le résumé, 
        # mais on peut aussi boucler sur les sous-domaines si besoin.
        logger.info("🔍 Phase 2 : Identification des technologies (WebTech)...")
        tech_scanner = TechScanner()
        tech_data = tech_scanner.scan(target)
        if tech_data:
            results["technologies"] = tech_data

        # 3. ANALYSE HEADERS & WHOIS
        logger.info("🛡️ Phase 3 : Analyse de sécurité et WHOIS...")
        results["security_headers"] = HeaderAnalyzer().analyze(target)
        results["whois"] = WhoisLookup().get_info(target)

        # 4. DÉDUCTION WAF/CDN (basé sur les IPs ou les Headers)
        # Si une IP appartient à Cloudflare, on met à jour le champ
        if results["subdomains"]:
            # Logique simple de détection WAF
            first_ips = results["subdomains"][0].get('ips', [])
            if any("104." in ip for ip in first_ips): # Exemple pour Cloudflare
                results["cdn_waf"] = "Cloudflare"

        logger.info(f"✅ Scan terminé : {len(results['subdomains'])} cibles identifiées.")
        return results

    except Exception as e:
        logger.error(f"❌ Erreur moteur : {str(e)}")
        return results
