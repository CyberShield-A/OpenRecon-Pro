"""
OpenRecon Pro — Flask Backend
"""
import io
import os
import json
import threading
import uuid
import tempfile
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
CORS(app, resources={r"/api/*": {"origins": "*"}})

FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")
_scan_results: dict = {}
_scan_lock = threading.Lock()

def _clean_domain(raw: str) -> str:
    domain = raw.strip()
    for prefix in ("https://", "http://"):
        if domain.lower().startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0].strip()
    ext = tldextract.extract(domain)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return domain

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path: str):
    if not os.path.isdir(FRONTEND_BUILD):
        return "<h1>Frontend non compilé</h1>", 503
    if path and os.path.isfile(os.path.join(FRONTEND_BUILD, path)):
        return send_from_directory(FRONTEND_BUILD, path)
    return send_from_directory(FRONTEND_BUILD, "index.html")

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(silent=True) or {}
    raw_target = data.get("target", "").strip()
    mode = data.get("mode", "NORMAL").upper()
    if not raw_target:
        return jsonify({"error": "Target requise"}), 400
    
    target = _clean_domain(raw_target)
    try:
        results = run(target=target, mode=mode)
        scan_id = str(uuid.uuid4())
        results["scan_date"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        with _scan_lock:
            _scan_results[scan_id] = results
        return jsonify({"scan_id": scan_id, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id: str, fmt: str):
    with _scan_lock:
        results = _scan_results.get(scan_id)
    if not results:
        return jsonify({"error": "ID inconnu"}), 404

    target = results.get("target", "scan").replace(".", "_")
    
    # Correction Bandit B108 : Utilisation de tempfile au lieu de /tmp/ statique
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if fmt == "json":
            with open(tmp_path, "w") as f:
                json.dump(results, f)
            return send_file(tmp_path, as_attachment=True, download_name=f"{target}.json")
        elif fmt == "txt":
            with open(tmp_path, "w") as f:
                f.write(str(results))
            return send_file(tmp_path, as_attachment=True, download_name=f"{target}.txt")
    finally:
        # Nettoyage après envoi si nécessaire (géré par le système ou manuellement)
        pass

if __name__ == "__main__":
    # Correction B104 : Indispensable pour Docker
    port = int(get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
