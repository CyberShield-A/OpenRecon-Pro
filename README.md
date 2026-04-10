# 🔎 OpenRecon Pro

OpenRecon Pro est un framework de **reconnaissance passive (OSINT)** léger, modulaire et extensible, écrit en Python. Il permet d'auditer la surface d'exposition d'un domaine et génère automatiquement un **rapport IA** compréhensible par du personnel non technique.

---

## ✨ Fonctionnalités

| Module | Description |
|---|---|
| 🔍 Sous-domaines | Découverte via crt.sh (passif) + brute-force DNS (actif) |
| 🌐 Résolution DNS | Résolution multi-thread avec score de confiance |
| 🛡️ WAF / CDN | Détection Cloudflare, Akamai, Fastly, Sucuri, etc. |
| 🃏 Wildcard DNS | Détection des zones DNS avec wildcard actif |
| 📋 RDAP | Lookup du domaine via RDAP (HTTP/JSON — sans blocage réseau) |
| 🔒 Headers HTTP | Audit de 7 en-têtes de sécurité avec score A → F |
| 🧬 Technologies | Fingerprinting serveur, CMS, frameworks, analytics, cookies |
| 🤖 Rapport IA | Rapport Ollama en français, destiné aux décideurs non techniques |
| 📄 Export HTML | Export du rapport en page HTML stylisée, prête à partager |
| 💾 Export JSON | Export complet des résultats bruts |

---

## 📦 Installation

```bash
git clone https://github.com/CyberShield-A/OpenRecon-Pro.git
cd OpenRecon-Pro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration (`.env`)

Copiez le fichier de configuration et adaptez-le :

```bash
cp .env.example .env
```

| Variable | Valeur par défaut | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.1:8b` | Modèle Ollama utilisé pour le rapport |
| `OLLAMA_HOST` | `http://localhost:11434` | Adresse du serveur Ollama |
| `GUI_PORT` | `8080` | Port de l'interface web |
| `DEFAULT_SCAN_MODE` | `NORMAL` | Mode de scan par défaut |
| `REQUEST_TIMEOUT` | `10` | Timeout HTTP (secondes) |

### Prérequis pour le rapport IA (optionnel)

```bash
# Installer Ollama : https://ollama.com
ollama pull llama3.1:8b
ollama serve
```

---

## 🖥️ Utilisation

### CLI — scan simple

```bash
python recon.py example.com
```

### CLI — scan avec rapport IA + export HTML

```bash
python recon.py example.com --report rapport.txt
# Génère automatiquement rapport.txt ET rapport.html
```

### Toutes les options CLI

```bash
python recon.py <cible> [--output fichier.json] [--limit N] [--stealth] [--aggressive] [--report <fichier.txt>]
```

| Option | Description |
|---|---|
| `--output` | Exporte les résultats en JSON |
| `--limit N` | Nombre max de liens analysés |
| `--stealth` | Mode furtif (moins de requêtes) |
| `--aggressive` | Mode agressif (plus de threads) |
| `--report` | Génère le rapport IA (`.txt` + `.html`) |

> **Note** : Le modèle Ollama est défini uniquement dans `.env` côté backend — il n'est pas exposé à l'interface.

### Interface Web (GUI)

```bash
python gui.py
```

Ouvre le navigateur sur `http://localhost:8080` (port configurable dans `.env`).

---

## 📁 Structure du projet

```
OpenRecon-Pro/
├── .env.example          # Template de configuration
├── .env.example          # Template de configuration
├── recon.py              # Point d'entrée principal (CLI avancée)
├── cli.py                # CLI simplifiée
├── gui.py                # Interface Web (NiceGUI)
├── core/
│   └── engine.py         # Moteur d'orchestration (tous les modules)
├── modules/
│   ├── contact.py        # Extraction téléphones / IPs
│   ├── email.py          # Extraction emails
│   ├── search.py         # Recherche Bing (filtrage URLs internes)
│   ├── report.py         # Rapport IA (Ollama) + export HTML
│   ├── whois_lookup.py   # Lookup RDAP du domaine (sans port 43)
│   ├── detection/
│   │   ├── waf_cdn.py    # Détection WAF / CDN
│   │   ├── wildcard.py   # Détection Wildcard DNS
│   │   ├── headers.py    # Audit des en-têtes de sécurité HTTP
│   │   └── tech.py       # Détection de technologies
│   └── subdomain/
│       ├── deep_scan.py  # Scan profond de sous-domaines
│       ├── resolver.py   # Résolution DNS
│       └── sources.py    # Sources (crt.sh, brute-force)
└── utils/
    ├── logger.py         # Affichage coloré
    └── config.py         # Chargement de la configuration (.env)
```

---

## 🔐 Sécurité & bonnes pratiques

- Le fichier `.env` **ne doit pas être versionné** (il est exclu par `.gitignore`)
- Le modèle Ollama est défini **uniquement côté backend** — l'interface web ne peut pas le modifier
- Toutes les requêtes utilisent HTTPS ; RDAP remplace WHOIS (port 43 souvent bloqué)
- Aucune donnée de scan n'est envoyée à un service externe

---

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE).
