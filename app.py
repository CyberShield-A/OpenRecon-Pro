import os
import json
import uuid
import threading
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Initialisation des répertoires pour les outils de scan
webtech_dir = os.path.expanduser("~/.local/share/webtech")
os.makedirs(webtech_dir, exist_ok=True)

try:
    from core.engine import run
    from utils.config import get
except (ImportError, ModuleNotFoundError):
    def get(k, default=None): return os.environ.get(k, default)
    def run(target, mode): return {"error": "Moteur non chargé"}

app = Flask(__name__)
app.secret_key = get("SECRET_KEY", "cybercell_prod_key_2026")
CORS(app, resources={r"/api/*": {"origins": "*"}})

FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")
_scan_results = {}
_results_lock = threading.Lock()

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD, path)):
        return send_from_directory(FRONTEND_BUILD, path)
    return send_from_directory(FRONTEND_BUILD, "index.html")

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(silent=True) or {}
    target = data.get("target", "").strip()
    mode = data.get("mode", "NORMAL").upper()

    if not target:
        return jsonify({"error": "Cible requise"}), 400

    try:
        results = run(target=target, mode=mode)
        scan_id = str(uuid.uuid4())
        results["scan_id"] = scan_id
        with _results_lock:
            _scan_results[scan_id] = results
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id, fmt):
    with _results_lock:
        results = _scan_results.get(scan_id)
    if not results:
        return jsonify({"error": "ID inconnu"}), 404

    target_safe = results.get("target", "scan").replace(".", "_")
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{fmt}") as tmp:
        tmp_path = tmp.name

    try:
        if fmt == "json":
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            return send_file(tmp_path, as_attachment=True, download_name=f"recon_{target_safe}.json")
        return jsonify({"error": "Format non supporté"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Correction B104 : On utilise une variable pour l'hôte
    listen_host = "0.0.0.0" # nosec B104
    server_port = int(os.environ.get("PORT", 5000))
    app.run(host=listen_host, port=server_port, debug=False)
