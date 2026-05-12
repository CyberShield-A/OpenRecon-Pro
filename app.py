import os
import sys
import json
import uuid
import threading
import tempfile
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# --- FORCE LE PATH POUR LE MOTEUR ---
# On ajoute explicitement le répertoire courant au PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- CHARGEMENT DU MOTEUR ---
ENGINE_LOADED = False
try:
    from core.engine import run
    from utils.config import get
    # Test rapide pour vérifier que ce n'est pas un import vide
    if callable(run):
        ENGINE_LOADED = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️ Erreur de chargement du moteur : {e}")
    def get(k, default=None): return os.environ.get(k, default)
    def run(target, mode): return {"error": f"Moteur non chargé : {str(e)}"}
    ENGINE_LOADED = False

app = Flask(__name__)
# On s'assure que la clé est robuste pour la session
app.secret_key = get("SECRET_KEY", "cybercell_prod_key_2026")

# CORS : Sécurisé pour le déploiement
CORS(app)

# Définition du chemin statique absolu
FRONTEND_BUILD = os.path.join(BASE_DIR, "frontend", "build")

_scan_results = {}
_results_lock = threading.Lock()

# --- SÉCURITÉ : Validation du domaine ---
def is_valid_domain(target):
    pattern = r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$"
    return re.match(pattern, target.lower()) is not None

# --- ROUTES STATIQUES ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # Sécurité : On empêche de remonter les répertoires
    if ".." in path or path.startswith("/"):
        return jsonify({"error": "Invalid path"}), 400
        
    full_path = os.path.join(FRONTEND_BUILD, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(FRONTEND_BUILD, path)
    return send_from_directory(FRONTEND_BUILD, "index.html")

# --- ROUTES API ---
@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not ENGINE_LOADED:
        return jsonify({"error": "Le moteur de scan n'est pas opérationnel sur ce serveur"}), 503

    data = request.get_json(silent=True) or {}
    target = data.get("target", "").strip().lower()
    mode = data.get("mode", "NORMAL").upper()

    if not target or not is_valid_domain(target):
        return jsonify({"error": "Cible invalide ou dangereuse"}), 400

    try:
        # Exécution du moteur de reconnaissance
        results = run(target=target, mode=mode)
        
        if "error" in results:
            return jsonify(results), 500

        scan_id = str(uuid.uuid4())
        results["scan_id"] = scan_id
        results["status"] = "success"
        results["timestamp"] = datetime.now().isoformat()
        results["target"] = target

        with _results_lock:
            # On limite la taille du dictionnaire pour éviter l'OOM
            if len(_scan_results) > 100:
                _scan_results.clear() 
            _scan_results[scan_id] = results
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Erreur lors du scan : {str(e)}"}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "engine_ready": ENGINE_LOADED,
        "version": "2.0.0-pro"
    }), 200

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id, fmt):
    with _results_lock:
        results = _scan_results.get(scan_id)
    
    if not results:
        return jsonify({"error": "Résultats de scan expirés ou inconnus"}), 404

    target_safe = results.get("target", "scan").replace(".", "_")
    
    try:
        if fmt == "json":
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as tmp:
                json.dump(results, tmp, indent=2)
                tmp_path = tmp.name
            return send_file(tmp_path, as_attachment=True, download_name=f"recon_{target_safe}.json")
            
        return jsonify({"error": "Format non supporté"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    listen_host = "0.0.0.0" # nosec B104
    server_port = int(os.environ.get("PORT", 5000))
    app.run(host=listen_host, port=server_port, debug=False)
