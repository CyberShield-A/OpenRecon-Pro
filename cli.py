
import sys
from core.engine import run
from utils.logger import banner, success

def cli():
    banner()
    if len(sys.argv) < 2:
        print("Usage: openrecon <domain> [--aggressive] [--model <ollama_model>] [--report <fichier.txt>]")
        print("Example: openrecon google.com --model llama3 --report rapport.txt")
        sys.exit(1)

    target = sys.argv[1]
    mode = "NORMAL"
    ollama_model = None
    report_path = None

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

    results = run(target, mode=mode, live_output=True, ollama_model=ollama_model, report_path=report_path)

    success(f"Scan terminé : {len(results.get('subdomains', []))} sous-domaines trouvés.")

    # Afficher le rapport si généré
    if results.get("report"):
        print("\n" + "=" * 60)
        print("RAPPORT D'ANALYSE IA")
        print("=" * 60)
        print(results["report"])

if __name__ == "__main__":
    cli()