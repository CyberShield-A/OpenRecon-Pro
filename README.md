# OpenRecon Pro

OpenRecon Pro est un framework de **reconnaissance passive (OSINT)** modulaire, écrit en Python avec une interface web moderne en **SvelteKit**. Il audite la surface d'exposition d'un domaine et génère automatiquement un **rapport IA** compréhensible par tout type de profil (décideur, pentester, développeur, admin système).

---

## Fonctionnalités

| Module         | Description                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| Sous-domaines  | 4 sources passives (crt.sh, HackerTarget, AlienVault OTX) + brute-force DNS avec scoring de confiance pondéré |
| Résolution DNS | Résolution multi-thread, déduplication, pénalité wildcard automatique                                         |
| WAF / CDN      | Détection 3 méthodes : plages CIDR, headers CDN, headers WAF — 13+ providers                                  |
| Wildcard DNS   | Détection probabiliste par double sondage aléatoire                                                           |
| RDAP           | Lookup domaine via RDAP (HTTP/JSON) — pas de dépendance port 43                                               |
| Headers HTTP   | Audit 7 en-têtes avec scoring pondéré (A→F) + validation des valeurs                                          |
| Technologies   | ~1 800 signatures via webtech (Wappalyzer) — CMS, frameworks, CDN, analytics                                  |
| Rapport IA     | Ollama (llama3.1:8b) — adapté au profil utilisateur (5 rôles)                                                 |
| Export         | JSON · TXT · HTML · CSV · PDF (rapport IA) · PDF (analyse brute)                                              |
| Auto-détection | Entrée sous-domaine ou domaine racine détectée automatiquement                                                |
| Subscope       | Si sous-domaine fourni, énumération supplémentaire sur ce scope                                               |

---

## Installation

```bash
git clone https://github.com/Tiemtore-dev/OpenRecon-Pro.git
cd OpenRecon-Pro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration (`.env`)

```bash
cp .env.example .env
```

| Variable            | Défaut                   | Description                   |
| ------------------- | ------------------------ | ----------------------------- |
| `OLLAMA_MODEL`      | `llama3.1:8b`            | Modèle Ollama pour le rapport |
| `OLLAMA_HOST`       | `http://localhost:11434` | Adresse du serveur Ollama     |
| `PORT`              | `6000`                   | Port du backend Flask         |
| `DEFAULT_SCAN_MODE` | `NORMAL`                 | Mode de scan par défaut       |
| `REQUEST_TIMEOUT`   | `10`                     | Timeout HTTP (secondes)       |

### Prérequis rapport IA

```bash
# https://ollama.com
ollama pull llama3.1:8b
ollama serve
```

---

## Utilisation

### Interface Web (recommandée)

```bash
# Terminal 1 — Backend Flask
python app.py

# Terminal 2 — Frontend SvelteKit (développement)
cd frontend
npm install
npm run dev
```

Ouvre `http://localhost:5173` (dev) ou `http://localhost:6000` (prod après `npm run build`).

### CLI

```bash
# Scan simple
python recon.py example.com

# Scan avec rapport IA et export HTML
python recon.py example.com --report rapport.txt

# Options complètes
python recon.py <cible> [--output fichier.json] [--stealth] [--aggressive] [--report <fichier.txt>]
```

| Option         | Description                                      |
| -------------- | ------------------------------------------------ |
| `--output`     | Export JSON des résultats bruts                  |
| `--stealth`    | Mode furtif (moins de requêtes)                  |
| `--aggressive` | Mode agressif (plus de threads, plus de sources) |
| `--report`     | Génère le rapport IA `.txt` + `.html`            |

---

## Architecture

```
OpenRecon-Pro/
├── app.py                        # Backend Flask — API REST + serving SPA
├── recon.py                      # Point d'entrée CLI
├── requirements.txt
├── core/
│   └── engine.py                 # Orchestration du pipeline de scan
├── modules/
│   ├── report.py                 # Rapport IA (Ollama) + export HTML/PDF
│   ├── prompts.py                # Prompts système par rôle utilisateur
│   ├── whois_lookup.py           # Lookup RDAP
│   ├── detection/
│   │   ├── waf_cdn.py            # Détection WAF/CDN (3 méthodes)
│   │   ├── wildcard.py           # Détection Wildcard DNS
│   │   ├── headers.py            # Audit en-têtes HTTP (scoring pondéré)
│   │   └── tech.py               # Fingerprinting via webtech
│   └── subdomain/
│       ├── deep_scan.py          # Orchestration + scoring de confiance
│       ├── resolver.py           # Résolution DNS multi-thread
│       ├── sources.py            # Sources : crt.sh, HackerTarget, OTX, bruteforce
│       └── parent_lookup.py      # Extraction domaine racine
├── frontend/                     # Interface SvelteKit
│   ├── src/
│   │   ├── app.css               # Thème global (Tailwind, palette noir)
│   │   ├── lib/
│   │   │   ├── api.js            # Client HTTP vers le backend
│   │   │   ├── stores.js         # État global Svelte (scan, rapport, stats)
│   │   │   ├── markdown.js       # Rendu Markdown du rapport IA
│   │   │   └── components/
│   │   │       ├── ScanPanel.svelte      # Formulaire de scan + mode
│   │   │       ├── StatsBar.svelte       # 4 cartes de statistiques
│   │   │       ├── ResultsPanel.svelte   # Onglets résultats + export
│   │   │       ├── AIReport.svelte       # Rapport IA + PDF
│   │   │       └── ConsoleLog.svelte     # Journal en temps réel
│   │   └── routes/
│   │       ├── +layout.svelte    # Layout avec navbar
│   │       └── +page.svelte      # Page principale
│   ├── tailwind.config.js
│   ├── svelte.config.js
│   └── vite.config.js
└── utils/
    ├── logger.py                 # Affichage coloré CLI
    └── config.py                 # Chargement .env
```

---

## Modes de scan

| Mode         | Comportement                                                       |
| ------------ | ------------------------------------------------------------------ |
| `NORMAL`     | Équilibré — sources passives + brute-force limité (20 threads DNS) |
| `STEALTH`    | Discret — sources passives uniquement, délais entre requêtes       |
| `AGGRESSIVE` | Complet — toutes sources, 50 threads DNS, brute-force étendu       |

---

## Export des résultats

Depuis l'interface web, le sélecteur dans la barre d'onglets permet d'exporter :

| Format           | Contenu                                                                     |
| ---------------- | --------------------------------------------------------------------------- |
| JSON             | Résultats bruts complets (structure machine)                                |
| TXT              | Rapport texte lisible                                                       |
| HTML             | Page HTML stylisée des résultats                                            |
| CSV              | Liste des sous-domaines (sous-domaine, IPs, confiance)                      |
| PDF (analyse)    | Document A4 structuré : sous-domaines triés, WAF/CDN, WHOIS, headers, techs |
| PDF (rapport IA) | Document A4 narratif généré par Ollama pour le profil choisi                |

---

## Sécurité & bonnes pratiques

- Le fichier `.env` n'est pas versionné (exclu par `.gitignore`)
- Toutes les requêtes utilisent HTTPS — RDAP remplace WHOIS (port 43 souvent bloqué en entreprise)
- Le modèle Ollama est défini côté backend uniquement
- Aucune donnée de scan n'est envoyée à un service externe
- Les résultats sont stockés en mémoire RAM côté serveur (non persistés)

---

## Licence

MIT — voir [LICENSE](LICENSE).
