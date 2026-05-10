# modules/subdomain/deep_scan.py
import concurrent.futures
import time
from .sources import from_crtsh, from_hackertarget, from_alienvault, from_bruteforce
from .resolver import resolve_domain
from modules.detection.wildcard import detect_wildcard
from utils.logger import loading, info, warning

# Poids par source — modifiable facilement pour ajouter de nouvelles sources
SOURCE_WEIGHTS = {
    "crtsh":       60,   # certificat SSL public — très fiable
    "hackertarget": 45,  # agrégateur DNS passif — fiable
    "alienvault":  45,   # passive DNS OTX — fiable
    "bruteforce":  15,   # wordlist — probable mais non attesté
}

def calculate_confidence(sub, source_sets: dict, wildcard_ips: list | None = None) -> int:
    """
    Calcule un score de confiance 0-100 selon les sources qui confirment le sous-domaine.
    
    - Chaque source contribue son poids indépendamment.
    - Si le wildcard DNS est actif, les hits brute-force-only sont pénalisés à 0
      (leur IP correspond à celle du wildcard → faux positif probable).
    - Le score est plafonné à 100.
    """
    score = 0
    sources_matched = []

    for name, source_set in source_sets.items():
        if sub in source_set:
            score += SOURCE_WEIGHTS.get(name, 10)
            sources_matched.append(name)

    # Pénalité wildcard : si seul le brute-force a trouvé ce sous-domaine
    # et que le wildcard est actif → score = 0 (très probablement un faux positif)
    if wildcard_ips and sources_matched == ["bruteforce"]:
        return 0

    return min(score, 100)


def deep_subdomain_scan(target, mode="NORMAL", live_output=False):
    start = time.time()
    results = []

    # 0. Détection wildcard préalable (évite de polluer les résultats)
    loading(f"Vérification wildcard DNS pour {target}...")
    wildcard_active, wildcard_ips = detect_wildcard(target)
    if wildcard_active:
        warning(f"Wildcard DNS détecté sur {target} → les hits brute-force-only seront ignorés")
    else:
        wildcard_ips = None

    # 1. Collecte passive et brute-force en parallèle
    loading(f"Collecte passive multi-sources pour {target}...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        f_crt  = pool.submit(from_crtsh, target)
        f_ht   = pool.submit(from_hackertarget, target)
        f_otx  = pool.submit(from_alienvault, target)
        crtsh_set       = f_crt.result()
        hackertarget_set = f_ht.result()
        alienvault_set   = f_otx.result()

    brute_set = from_bruteforce(target)

    source_sets = {
        "crtsh":        crtsh_set,
        "hackertarget": hackertarget_set,
        "alienvault":   alienvault_set,
        "bruteforce":   brute_set,
    }

    # Statistiques de collecte
    info(f"crt.sh         : {len(crtsh_set)} domaines")
    info(f"HackerTarget   : {len(hackertarget_set)} domaines")
    info(f"AlienVault OTX : {len(alienvault_set)} domaines")
    info(f"Brute-force    : {len(brute_set)} candidats")

    candidates = crtsh_set | hackertarget_set | alienvault_set | brute_set
    info(f"Total candidats uniques à tester : {len(candidates)}")

    # 2. Résolution DNS en parallèle
    max_threads = 50 if mode == "AGGRESSIVE" else 20

    def worker(sub):
        ips = resolve_domain(sub)
        if not ips:
            return None
        confidence = calculate_confidence(sub, source_sets, wildcard_ips)
        if confidence == 0:
            return None   # faux positif wildcard → écarté
        return {
            "subdomain":  sub,
            "ips":        ips,
            "confidence": confidence,
            "sources":    [s for s, ss in source_sets.items() if sub in ss],
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(worker, s) for s in candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    duration = round(time.time() - start, 2)

    return {
        "results":  results,
        "total":    len(results),
        "duration": duration,
    }