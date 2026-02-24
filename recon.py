import sys
import json
import requests
from core.engine import run
from modules.search import search_b
from utils.logger import banner, loading, success, warning

def fetch_html(url):
    if not url.startswith(("http://","https://")):
        url = "https://" + url.lstrip("https://")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
        else:
            warning(f"Non-200 response from {url} ({r.status_code})")
    except:
        warning(f"Failed to fetch {url}")
    return ""

def main():
    banner()
    if len(sys.argv)<2:
        print("Usage: python main.py <target> [--output file.json] [--limit N]")
        sys.exit(1)

    target = sys.argv[1]
    output_file = None
    max_links = 10  # par défaut

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx+1 < len(sys.argv):
            output_file = sys.argv[idx+1]
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx+1 < len(sys.argv):
            try: max_links=int(sys.argv[idx+1])
            except: pass

    print(f"\n[+] Target: {target}")
    print("[+] Searching Bing...")
    links = search_b(target, limit=max_links)
    combined_html = ""
    for i, link in enumerate(links,1):
        loading(f"Fetching {i}/{len(links)}: {link}")
        combined_html += fetch_html(link)
    success("Fetching completed.")

    results = run(target, html=combined_html, base_url=target, live_output=True, max_pages=50)

    if output_file:
        with open(output_file,"w") as f:
            json.dump(results, f, indent=4)
        success(f"Results exported to {output_file}")

if __name__=="__main__":
    main()