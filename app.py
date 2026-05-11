import os
import json
import uuid
import threading
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# --- FIX CRITIQUE : WEBTECH / ENVIRONNEMENT ---
# On s'assure que les répertoires de données pour les outils de reconnaissance existent 
# pour éviter le FileNotFoundError (Errno 2) vu au Build #96.
webtech_dir = os.path.expanduser("~/.local/share/webtech")
if not os.path.exists(webtech_dir):
    os.makedirs(webtech_dir, exist_ok=True)

try:
    from core.engine import run
    from utils.config import get
except (ImportError, ModuleNotFoundError) as e:
    print(f"[-] Erreur lors du chargement des modules : {e}")
    # Fallback pour éviter le crash au démarrage si le moteur n'est pas encore prêt
    def get(k, default=None): return os.environ.get(k, default)
    def run(target, mode): return {"error": "Moteur non chargé", "details": str(e)}

app = Flask(__name__)
app.secret_key = get("SECRET_KEY", "openrecon_default_secure_key_2026")

# Activation de CORS pour permettre au frontend de communiquer avec l'API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Chemin vers le build du frontend SvelteKit
FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")

# Stockage temporaire des résultats en mémoire
_scan_results = {}
_results_lock = threading.Lock()

# --- ROUTES FRONTEND ---

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """Sert l'application Single Page Application (SPA)."""
    if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD, path)):
        return send_from_directory(FRONTEND_BUILD, path)
    return send_from_directory(FRONTEND_BUILD, "index.html")

# --- ROUTES API RECONNAISSANCE ---

@app.route("/api/scan", methods=["POST"])
def api_scan():
    """Point d'entrée pour lancer un scan de reconnaissance complet."""
    data = request.get_json(silent=True) or {}
    target = data.get("target", "").strip()
    mode = data.get("mode", "NORMAL").upper()

    if not target:
        return jsonify({"error": "Une cible (domaine ou IP) est requise"}), 400

    try:
        # Appel du moteur de scan (exécute Nmap, Subdomain scan, etc.)
        results = run(target=target, mode=mode)
        
        scan_id = str(uuid.uuid4())
        results["scan_id"] = scan_id
        results["timestamp"] = datetime.now().isoformat()

        # Sauvegarde sécurisée par thread-lock
        with _results_lock:
            _scan_results[scan_id] = results

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'exécution du scan : {str(e)}"}), 500

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id, fmt):
    """Génère et envoie le rapport de scan dans le format demandé."""
    with _results_lock:
        results = _scan_results.get(scan_id)
    
    if not results:
        return jsonify({"error": "Résultats introuvables"}), 404

    target_safe = results.get("target", "scan").replace(".", "_")
    
    # Correction Bandit B108 : Utilisation de tempfile sécurisé
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{fmt}") as tmp:
        tmp_path = tmp.name

    try:
        if fmt == "json":
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            return send_file(tmp_path, as_attachment=True, download_name=f"report_{target_safe}.json")
        
        elif fmt == "txt":
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(f"OPENRECON-PRO REPORT - {target_safe}\n")
                f.write("="*50 + "\n")
                f.write(json.dumps(results, indent=2))
            return send_file(tmp_path, as_attachment=True, download_name=f"report_{target_safe}.txt")
        
        return jsonify({"error": "Format non supporté"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DÉMARRAGE DU SERVEUR ---

if __name__ == "__main__":
    # Récupération du port via variable d'environnement (prioritaire pour Docker/Terraform)
    # Mapping Terraform : 8081 (externe) -> 5000 (interne)
    server_port = int(os.environ.get("PORT", 5000))
    
    # Binding sur 0.0.0.0 indispensable pour être accessible depuis le réseau Docker
    # Debug=False en production pour éviter les failles de sécurité
    print(f"[*] OpenRecon-Pro démarré sur http://0.0.0.0:{server_port}")
    app.run(host="0.0.0.0", port=server_port, debug=False)
