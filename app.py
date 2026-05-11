"""
OpenRecon Pro — Flask Backend
Point d'entrée principal de l'application web.
"""
import io
import os
import json
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import tldextract

from core.engine import run
from modules.subdomain.deep_scan import deep_subdomain_scan
from modules.report import generate_report, export_html_string, export_pdf_html_string
from modules.subdomain.parent_lookup import find_parent_domain
from utils.config import get

app = Flask(__name__)
app.secret_key = get("SECRET_KEY", os.urandom(32))
# Autorise CORS pour faciliter les tests Jenkins/DevOps
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SvelteKit compiled output (run: cd frontend && npm run build)
FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")

# Stockage temporaire des scans en cours et résultats
_scan_results: dict = {}
_scan_lock = threading.Lock()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_domain(raw: str) -> str:
    """Normalise une URL ou un domaine brut en domaine racine."""
    domain = raw.strip()
    for prefix in ("https://", "http://"):
        if domain.lower().startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0].strip()

    # Auto-détection : si l'entrée est un sous-domaine, extraire le domaine racine
    ext = tldextract.extract(domain)
    if ext.domain and ext.suffix:
        registered = f"{ext.domain}.{ext.suffix}"
        return registered  # ex: api.github.com → github.com
    return domain


# ─── SvelteKit SPA ────────────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path: str):
    """Sert l'application SvelteKit (adapter-static)."""
    if not os.path.isdir(FRONTEND_BUILD):
        return (
            "<h1 style='font-family:monospace;padding:2rem'>Frontend non compilé</h1>"
            "<p style='font-family:monospace;padding:0 2rem'>"
            "Exécutez : <code>cd frontend && npm install && npm run build</code></p>",
            503,
        )
    # Serve static assets (JS, CSS, _app/, …)
    if path:
        full = os.path.join(FRONTEND_BUILD, path)
        if os.path.isfile(full):
            return send_from_directory(FRONTEND_BUILD, path)
    # SPA fallback → index.html handles client-side routing
    return send_from_directory(FRONTEND_BUILD, "index.html")


# ─── API Scan ─────────────────────────────────────────────────────────────────

@app.route("/api/scan", methods=["POST"])
def api_scan():
    """Lance un scan complet sur le domaine cible."""
    data = request.get_json(silent=True) or {}
    raw_target = data.get("target", "").strip()
    mode = data.get("mode", "NORMAL").upper()

    if not raw_target:
        return jsonify({"error": "Le champ 'target' est requis."}), 400

    target = _clean_domain(raw_target)
    if not target or "." not in target:
        return jsonify({"error": "Domaine invalide. Exemple : google.com"}), 400

    # Détecter si l'utilisateur avait entré un sous-domaine
    _ext = tldextract.extract(raw_target.strip().split("//")[-1].split("/")[0])
    subdomain_input = bool(_ext.subdomain)

    if mode not in ("NORMAL", "STEALTH", "AGGRESSIVE"):
        mode = "NORMAL"

    try:
        results = run(target=target, mode=mode)

        for sub in results.get("subdomains", []):
            sub.setdefault("scope", "root")

        if subdomain_input and _ext.subdomain and _ext.domain and _ext.suffix:
            original_sub = f"{_ext.subdomain}.{_ext.domain}.{_ext.suffix}"
            try:
                sub_data = deep_subdomain_scan(target=original_sub, mode=mode)
                existing = {s["subdomain"] for s in results["subdomains"]}
                for entry in sub_data.get("results", []):
                    entry["scope"] = "subscope"
                    if entry["subdomain"] not in existing:
                        results["subdomains"].append(entry)
                        existing.add(entry["subdomain"])
                results["subscope_target"] = original_sub
            except Exception as sub_err:
                results["subscope_error"] = str(sub_err)

        results["target"] = target
        results["target_input"] = raw_target.strip()
        results["subdomain_input"] = subdomain_input
        results["mode"] = mode
        results["scan_date"] = datetime.now().strftime("%d/%m/%Y à %H:%M")

        scan_id = str(uuid.uuid4())
        with _scan_lock:
            _scan_results[scan_id] = results

        return jsonify({"scan_id": scan_id, "results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── API Rapport IA ───────────────────────────────────────────────────────────

@app.route("/api/report", methods=["POST"])
def api_report():
    """Génère un rapport IA adapté au profil utilisateur."""
    data = request.get_json(silent=True) or {}
    scan_id = data.get("scan_id", "")
    user_role = data.get("user_role", "chef_entreprise")
    scan_type = data.get("scan_type", "complet")
    model = data.get("model", None)

    with _scan_lock:
        results = _scan_results.get(scan_id)

    if not results:
        return jsonify({"error": "scan_id introuvable."}), 404

    report_text = generate_report(
        target=results.get("target", "inconnu"),
        results=results,
        user_role=user_role,
        scan_type=scan_type,
        model=model
    )

    if not report_text:
        return jsonify({"error": "Erreur Ollama."}), 503

    with _scan_lock:
        if scan_id in _scan_results:
            _scan_results[scan_id]["report"] = report_text
            _scan_results[scan_id]["report_role"] = user_role

    return jsonify({"report": report_text, "role": user_role})


# ─── API Parent Domain ────────────────────────────────────────────────────────

@app.route("/api/parent-domain", methods=["POST"])
def api_parent_domain():
    data = request.get_json(silent=True) or {}
    subdomain = data.get("subdomain", "").strip()
    if not subdomain:
        return jsonify({"error": "Requis"}), 400
    subdomain = _clean_domain(subdomain)
    return jsonify(find_parent_domain(subdomain))


# ─── API Téléchargement ───────────────────────────────────────────────────────

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id: str, fmt: str):
    with _scan_lock:
        results = _scan_results.get(scan_id)

    if not results:
        return jsonify({"error": "ID introuvable"}), 404

    target = results.get("target", "scan")
    safe_target = target.replace(".", "_")
    fmt = fmt.lower()

    if fmt == "json":
        filename = f"openrecon_{safe_target}.json"
        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        return send_file(tmp_path, as_attachment=True, download_name=filename, mimetype="application/json")

    elif fmt == "txt":
        filename = f"openrecon_{safe_target}.txt"
        tmp_path = f"/tmp/{filename}"
        content = _results_to_txt(results)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(tmp_path, as_attachment=True, download_name=filename, mimetype="text/plain")

    elif fmt == "pdf":
        filename = f"openrecon_{safe_target}_rapport.pdf"
        report_text = results.get("report", "")
        if not report_text:
            return jsonify({"error": "Générez le rapport d'abord"}), 400
        html = export_pdf_html_string(report_text, target, user_role=results.get("report_role", ""))
        try:
            from weasyprint import HTML as WeasyprintHTML
            pdf_bytes = WeasyprintHTML(string=html).write_pdf()
            return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype="application/pdf")
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif fmt == "csv":
        filename = f"openrecon_{safe_target}_subdomains.csv"
        tmp_path = f"/tmp/{filename}"
        content = _subdomains_to_csv(results)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(tmp_path, as_attachment=True, download_name=filename, mimetype="text/csv")

    return jsonify({"error": "Format non supporté"}), 400


# ─── Helpers de conversion (Extraits) ──────────────────────────────────────────

def _results_to_txt(results: dict) -> str:
    lines = [f"OPENRECON PRO — Cible : {results.get('target')}", "-"*30]
    for s in results.get("subdomains", []):
        lines.append(f"{s.get('subdomain')} | {s.get('ips')}")
    return "\n".join(lines)

def _subdomains_to_csv(results: dict) -> str:
    lines = ["subdomain,ips,confidence"]
    for s in results.get("subdomains", []):
        ips = " ".join(s.get("ips", []))
        lines.append(f"{s.get('subdomain')},{ips},{s.get('confidence')}")
    return "\n".join(lines)


# ─── Point d'entrée (CORRIGÉ POUR DOCKER) ──────────────────────────────────────

if __name__ == "__main__":
    # Récupère les variables d'environnement (Terraform/Docker)
    debug_mode = get("FLASK_DEBUG", "false").lower() == "true"
    
    # Port 5000 est celui attendu en interne par ton Terraform (internal = 5000)
    server_port = int(get("PORT", "5000")) 
    
    print(f"[*] Démarrage du serveur OpenRecon sur le port {server_port}...")
    print(f"[*] Binding sur 0.0.0.0 pour l'accessibilité Docker")
    
    # IMPORTANT : host="0.0.0.0" est obligatoire pour que le mappage 
    # de port Docker (8081 -> 5000) fonctionne.
    app.run(host="0.0.0.0", port=server_port, debug=debug_mode)
