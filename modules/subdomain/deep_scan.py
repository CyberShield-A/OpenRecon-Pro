# modules/subdomain/deep_scan.py
import concurrent.futures
import time
from .sources import from_crtsh, from_bruteforce
from .resolver import resolve_domain
from utils.logger import loading, info

def calculate_confidence(sub, passive, brute):
    score = 0
    if sub in passive: score += 70
    if sub in brute: score += 30
    return min(score, 100)

def deep_subdomain_scan(target, mode="NORMAL", live_output=False):
    start = time.time()
    results = []

    # 1. Collecte des candidats
    loading(f"Collecte passive pour {target}...")
    passive = from_crtsh(target)
    print(f"[DEBUG] Crt.sh a trouvé : {len(passive)} domaines") # Pour debug dans PowerShell

    loading(f"Génération brute-force pour {target}...")
    brute = from_bruteforce(target)
    
    candidates = passive.union(brute)
    print(f"[DEBUG] Total candidats à tester : {len(candidates)}")

    # 2. Résolution DNS en parallèle
    max_threads = 50 if mode == "AGGRESSIVE" else 20
    
    def worker(sub):
        ips = resolve_domain(sub)
        if ips:
            return {
                "subdomain": sub,
                "ips": ips,
                "confidence": calculate_confidence(sub, passive, brute)
            }
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(worker, s) for s in candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    duration = round(time.time() - start, 2)
    
    # ⚡ IMPORTANT : Retourner le dictionnaire avec la clé 'results'
    return {
        "results": results,
        "total": len(results),
        "duration": duration
    }