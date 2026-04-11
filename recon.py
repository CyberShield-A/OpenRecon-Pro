import sys
import os
import json
import requests
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import run
from modules.search import search_b
from utils.logger import banner, loading, success, warning

logger = logging.getLogger(__name__)

def fetch_html(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            return r.text
        else:
            warning(f"Non-200 response from {url} ({r.status_code})")
            return ""

    except requests.RequestException as e:
        logger.warning(f"Erreur réseau pour {url}: {e}")
    except Exception as e:
        logger.exception(f"Erreur inattendue dans fetch_html({url})")

    return ""


def clean_bing_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    if "u" in query:
        decoded = urllib.parse.unquote(query["u"][0])
        return decoded

    return url


def fetch_all_html(links, max_threads=5):
    combined_html = ""

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(fetch_html, link): link for link in links}

        for i, future in enumerate(as_completed(futures), 1):
            link = futures[future]
            loading(f"Fetching {i}/{len(links)}: {link}")

            try:
                combined_html += future.result()
            except Exception as e:
                logger.error(f"Erreur thread sur {link}: {e}")

    return combined_html


def main():
    banner()

    if len(sys.argv) < 2:
        print("Usage: python recon.py <target> [--output file.json] [--limit N] [--stealth] [--aggressive] [--model <ollama_model>] [--report <fichier.txt>]")
        sys.exit(1)

    target = sys.argv[1]
    output_file = None
    max_links = 10
    mode = "NORMAL"
    ollama_model = None
    report_path = None

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            try:
                max_links = int(sys.argv[idx + 1])
            except ValueError as e:
                warning(f"Valeur invalide pour --limit: {sys.argv[idx + 1]}")
                logger.warning(f"Erreur conversion --limit: {e}")

    if "--stealth" in sys.argv:
        mode = "STEALTH"
    if "--aggressive" in sys.argv:
        mode = "AGGRESSIVE"

    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            ollama_model = sys.argv[idx + 1]

    if "--report" in sys.argv:
        idx = sys.argv.index("--report")
        if idx + 1 < len(sys.argv):
            report_path = sys.argv[idx + 1]

    print(f"\n[+] Target: {target}")
    print(f"[+] Mode: {mode}")
    print("[+] Searching Bing...")

    raw_links = search_b(target, limit=max_links)
    links = [clean_bing_url(u) for u in raw_links]

    combined_html = fetch_all_html(links, max_threads=5)
    success("Fetching completed.")

    results = run(
        target,
        mode=mode,
        live_output=True,
        ollama_model=ollama_model,
        report_path=report_path
    )

    final_results = {
        "target": target,
        "recon_results": results
    }

    if output_file:
        try:
            with open(output_file, "w") as f:
                json.dump(final_results, f, indent=4)
            success(f"Results exported to {output_file}")

        except OSError as e:
            warning(f"Failed to export JSON: {str(e)}")
            logger.error(f"Erreur écriture fichier {output_file}: {e}")

    total_subs = len(results.get("subdomains", []))
    print(f"\n[+] Recon completed: {total_subs} valid subdomains found.")

    for sub in results.get("subdomains", []):
        sub_name = sub.get("subdomain", "N/A")
        ips = ",".join(sub.get("ips", [])) if sub.get("ips") else "N/A"
        conf = sub.get("confidence", 0)
        cdn = sub.get("cdn") or "-"
        waf = sub.get("waf") or "-"

        print(f"[SUBDOMAIN] {sub_name} | IPs: {ips} | Confidence: {conf}% | CDN: {cdn} | WAF: {waf}")

    if results.get("report"):
        print("\n" + "=" * 60)
        print("RAPPORT D'ANALYSE IA")
        print("=" * 60)
        print(results["report"])


if __name__ == "__main__":
    main()