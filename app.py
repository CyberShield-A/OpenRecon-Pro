import os
import json
import uuid
import threading
import tempfile
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Importation sécurisée du moteur de scan
try:
    from core.engine import run
    from utils.config import get
except (ImportError, ModuleNotFoundError):
    def get(k, default=None): return os.environ.get(k, default)
    def run(target, mode): return {"error": "Moteur non chargé"}

app = Flask(__name__)
# Sécurisation de la clé secrète via variable d'environnement
app.secret_key = get("SECRET_KEY", "cybercell_prod_key_2026")

# CONFIGURATION DEVOPS : Autorise le frontend sur le port 8081 à lire l'API
CORS(app, resources={r"/api/*": {"origins": "*"}})

FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")

# Stockage des résultats (Utilise un dictionnaire partagé pour l'interface graphique)
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
    """Point d'entrée principal pour l'interface graphique"""
    data = request.get_json(silent=True) or {}
    target = data.get("target", "").strip()
    mode = data.get("mode", "NORMAL").upper()

    if not target:
        return jsonify({"error": "Cible requise"}), 400

    try:
        # Lancement du scan via engine.py
        results = run(target=target, mode=mode)
        
        # Génération d'un ID unique pour le suivi dans l'interface
        scan_id = str(uuid.uuid4())
        results["scan_id"] = scan_id
        results["status"] = "completed"
        results["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sauvegarde en mémoire pour récupération par l'interface
        with _results_lock:
            _scan_results[scan_id] = results
        
        # On renvoie l'objet COMPLET pour peupler les tableaux de bord immédiatement
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/results/<scan_id>", methods=["GET"])
def get_results(scan_id):
    """Permet au Frontend de rafraîchir les données d'un scan spécifique"""
    with _results_lock:
        results = _scan_results.get(scan_id)
    if not results:
        return jsonify({"error": "Résultats introuvables"}), 404
    return jsonify(results)

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id, fmt):
    with _results_lock:
        results = _scan_results.get(scan_id)
    if not results:
        return jsonify({"error": "ID inconnu"}), 404

    target_safe = results.get("target", "scan").replace(".", "_")
    
    # Utilisation de tempfile pour éviter les conflits de droits Docker
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

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "online", "version": "v2.0"}), 200

if __name__ == "__main__":
    # Paramètres réseau compatibles avec Docker et Terraform
    listen_host = "0.0.0.0" 
    server_port = int(os.environ.get("PORT", 5000))
    app.run(host=listen_host, port=server_port, debug=False)
