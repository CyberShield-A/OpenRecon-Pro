# utils/config.py
"""Charge la configuration depuis le fichier .env à la racine du projet."""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE = os.path.join(_ROOT, ".env")

def _load_env():
    env = {}
    if not os.path.exists(_ENV_FILE):
        return env
    with open(_ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env

_CONFIG = _load_env()

def get(key, default=None):
    """Retourne la valeur de la clé depuis .env, puis les variables d'environnement système, puis la valeur par défaut."""
    return _CONFIG.get(key) or os.environ.get(key) or default
