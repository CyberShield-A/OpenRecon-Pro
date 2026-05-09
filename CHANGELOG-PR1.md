# Changelog — Pull Request #1

## feat: SvelteKit frontend + backend improvements v2

> Session de développement — Mai 2026  
> Branche : `feature/improvements-v2` → `main`

---

## 1. Interface Web — SvelteKit (nouveau)

L'ancienne interface NiceGUI (`gui.py`) a été remplacée par une SPA **SvelteKit 2 + Svelte 5 + Tailwind CSS 3.4 + Vite**, servie statiquement par Flask après build.

### Architecture frontend

- **`app.py`** — Backend Flask découplé (API REST + serving SPA)
- **`frontend/src/lib/api.js`** — Client HTTP centralisé (`const BASE = '/api'`)
- **`frontend/src/lib/stores.js`** — État global réactif (scan, rapport, stats dérivées)
- **`frontend/src/lib/markdown.js`** — Rendu Markdown du rapport IA en HTML sécurisé

### Composants

| Composant             | Rôle                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| `ScanPanel.svelte`    | Formulaire de scan avec sélecteur de mode (Normal / Stealth / Agressif)                         |
| `StatsBar.svelte`     | 4 cartes : sous-domaines, WAF/CDN (CDN + WAF séparés + badge méthode), wildcard, score sécurité |
| `ResultsPanel.svelte` | Onglets : Sous-domaines · WHOIS/RDAP · Technologies · En-têtes HTTP + sélecteur d'export        |
| `AIReport.svelte`     | Rapport IA : sélection rôle (5 profils) + type d'analyse + bouton Copier + bouton PDF           |
| `ConsoleLog.svelte`   | Journal temps réel des étapes du scan                                                           |

### Thème vrai-noir

Remplacement complet de la palette GitHub (`#0d1117` / `#161b22` / `#21262d`) par une palette noir pur :

| Rôle                            | Avant     | Après     |
| ------------------------------- | --------- | --------- |
| Fond principal (`surface`)      | `#0d1117` | `#000000` |
| Panneaux (`panel`)              | `#161b22` | `#080808` |
| Éléments surélevés (`elevated`) | `#21262d` | `#0f0f0f` |
| Bordures                        | `#30363d` | `#1c1c1c` |
| Hover fond                      | `#2d333b` | `#141414` |
| Hover bordure                   | `#484f58` | `#272727` |
| Texte atténué                   | `#8b949e` | `#555555` |
| Texte très atténué              | `#6e7681` | `#3a3a3a` |
| Texte secondaire                | `#c9d1d9` | `#b8b8b8` |
| Texte principal                 | `#e6edf3` | `#e8e8e8` |

Remplacement appliqué sur l'ensemble des fichiers `.svelte`, `.css`, `.js`, `app.html` et `tailwind.config.js` en une seule passe (`sed`).

---

## 2. Détection WAF / CDN — `modules/detection/waf_cdn.py`

**Avant** : détection basique par headers, retournait une chaîne.

**Après** : 3 méthodes de détection, retourne un dict structuré `{cdn, waf, method, ips}`.

### Méthodes

1. **Plages CIDR** — Résolution DNS de la cible → comparaison avec les plages IP connues (Cloudflare : 15 plages, Akamai, Fastly, CloudFront, Azure CDN)
2. **Headers CDN** — 10 providers : `CF-Ray`, `X-Fastly-Request-Id`, `X-Amz-Cf-Id`, `X-Azure-Ref`, etc.
3. **Headers WAF** — 13 providers : Imperva, Sucuri, F5 BIG-IP, Barracuda, Fortinet, AWS WAF, Wallarm, Reblaze, etc.

### Format de sortie

```json
{
  "cdn": "Cloudflare",
  "waf": "Imperva",
  "method": "ip_range+header",
  "ips": ["104.21.x.x"]
}
```

La `StatsBar` affiche CDN et WAF sur deux lignes séparées avec un badge de méthode (`IP` / `HDR` / `IP+HDR`).

---

## 3. Audit en-têtes HTTP — `modules/detection/headers.py`

**Avant** : présence/absence simple, pas de validation des valeurs.

**Après** : scoring pondéré (total 100 points) + validation des valeurs + grade A → F.

### Poids par en-tête

| En-tête                     | Poids | Validation                                  |
| --------------------------- | ----- | ------------------------------------------- |
| `Strict-Transport-Security` | 25    | `max-age ≥ 31 536 000`, `includeSubDomains` |
| `Content-Security-Policy`   | 25    | Détection `unsafe-inline`, `unsafe-eval`    |
| `X-Frame-Options`           | 15    | Doit être `DENY` ou `SAMEORIGIN`            |
| `X-Content-Type-Options`    | 15    | Doit être `nosniff`                         |
| `Referrer-Policy`           | 10    | Avertissement si politique permissive       |
| `Permissions-Policy`        | 8     | Présence                                    |
| `X-XSS-Protection`          | 2     | Déprécié, signalé                           |

### Scoring

- Valide → poids plein
- Avertissement → 60 % du poids
- Invalide/absent → 10 % du poids (compté comme manquant)

---

## 4. Détection de technologies — `modules/detection/tech.py`

**Avant** : 55 signatures manuelles codées en dur (regex sur headers + HTML).

**Après** : intégration de la bibliothèque **webtech** (enthec/webappanalyzer), qui embarque ~1 800 signatures actualisées couvrant CMS, frameworks, CDN, analytics, serveurs, langages, etc.

```python
wt = WebTech(options={"silent": True})
wt.output_format = Format["json"]          # doit être défini après instanciation
wt.USER_AGENT = secrets.choice(USER_AGENTS)
report = wt.start_from_url(f"https://{domain}", timeout=12)
```

---

## 5. Découverte de sous-domaines — `modules/subdomain/`

### Sources — `sources.py`

**Avant** : crt.sh uniquement.

**Après** : 4 sources collectées en parallèle (`ThreadPoolExecutor(3)`) :

| Source         | Poids de confiance | Type                             |
| -------------- | ------------------ | -------------------------------- |
| crt.sh         | 60                 | Passif (certificats SSL publics) |
| HackerTarget   | 45                 | Passif (agrégateur DNS)          |
| AlienVault OTX | 45                 | Passif (DNS passif)              |
| Brute-force    | 15                 | Actif (wordlist ~60 mots)        |

### Scoring de confiance — `deep_scan.py`

Chaque sous-domaine reçoit un score basé sur les sources qui le confirment (somme des poids, max 100).

Pénalité wildcard : si le wildcard DNS est actif **et** que seul le brute-force a trouvé le sous-domaine → score = 0 → écarté (faux positif probable).

### Scan subscope

Si l'utilisateur entre un sous-domaine (ex : `api.github.com`) :

1. Le domaine racine (`github.com`) est extrait automatiquement via `tldextract` et scanné complètement
2. Un second scan est lancé sur `api.github.com` pour découvrir ses propres fils (`v1.api.github.com`, `staging.api.github.com`, etc.)
3. Les résultats sont fusionnés, les duplicats supprimés, les entrées subscope taguées `scope: "subscope"` et affichées avec un badge violet `⬇ sub`

---

## 6. Auto-détection sous-domaine → domaine racine — `app.py`

**Avant** : l'utilisateur devait saisir uniquement le domaine racine.

**Après** : `_clean_domain()` utilise `tldextract` pour extraire automatiquement le domaine enregistré.

```
api.github.com   →   github.com  (scan lancé sur github.com)
https://sub.example.co.uk/path   →   example.co.uk
```

Le frontend affiche dans la console : `ℹ Sous-domaine détecté — scan lancé sur le domaine racine : github.com`

---

## 7. Export PDF — `app.py` + `modules/report.py`

Deux formats PDF distincts via **WeasyPrint** :

### PDF rapport IA — `GET /api/download/<id>/pdf`

- Appelle `export_pdf_html_string()` — template blanc A4 (`@page { size: A4; margin: 2.5cm 3cm }`)
- Fond blanc, texte `#1a1a1a`, titres bleu marine `#1e3a8a`
- S'étend sur toute la largeur de page (pas de `div` container limitant)
- Déclenché par le bouton **PDF** dans la toolbar du rapport IA (à côté de Copier)

### PDF analyse brute — `GET /api/download/<id>/scan-pdf`

- Appelle `_results_to_scan_pdf_html()` — génère des tableaux structurés
- Sections : sous-domaines triés par confiance, WAF/CDN, WHOIS/RDAP, en-têtes HTTP (avec score et grade), technologies
- Déclenché par le sélecteur **PDF** dans la tab bar des résultats

---

## 8. Sélecteur d'export dans ResultsPanel

**Avant** : `DownloadPanel` dans la sidebar avec des boutons séparés.

**Après** : sélecteur `<select>` + bouton **Exporter** intégré dans la barre d'onglets de `ResultsPanel`, visible uniquement quand un scan est disponible.

Formats disponibles : JSON · TXT · HTML · CSV · PDF (analyse).

---

## 9. Suppression de `ParentDomainTool`

L'onglet "Trouver le domaine parent" a été retiré de la sidebar — la détection est désormais entièrement automatique côté backend (voir point 6).

---

## 10. Rapport IA — profils et prompts — `modules/prompts.py`

Nouveau fichier centralisant les prompts système par rôle utilisateur :

| Rôle              | Adapté pour                                                        |
| ----------------- | ------------------------------------------------------------------ |
| `chef_entreprise` | Vue stratégique, risques métier, langage non technique             |
| `pentester`       | Détails techniques, vecteurs d'attaque, recommandations offensives |
| `admin_systeme`   | Actions correctives immédiates, configuration, patches             |
| `developpeur`     | Vulnérabilités code, headers manquants, intégration CI             |
| `etudiant`        | Pédagogique, explications, glossaire                               |

---

## 11. `.gitignore` mis à jour

Ajout des exclusions manquantes pour le frontend :

```
node_modules/
frontend/node_modules/
frontend/.svelte-kit/
frontend/build/
```

---

## Fichiers modifiés / créés

| Fichier                              | Statut                               |
| ------------------------------------ | ------------------------------------ |
| `app.py`                             | Nouveau                              |
| `modules/prompts.py`                 | Nouveau                              |
| `modules/subdomain/parent_lookup.py` | Nouveau                              |
| `frontend/` (ensemble)               | Nouveau                              |
| `core/engine.py`                     | Modifié                              |
| `modules/detection/headers.py`       | Réécrit                              |
| `modules/detection/tech.py`          | Réécrit                              |
| `modules/detection/waf_cdn.py`       | Réécrit                              |
| `modules/report.py`                  | Réécrit                              |
| `modules/subdomain/deep_scan.py`     | Réécrit                              |
| `modules/subdomain/sources.py`       | Réécrit                              |
| `modules/whois_lookup.py`            | Modifié                              |
| `requirements.txt`                   | Mis à jour (`webtech`, `weasyprint`) |
| `.gitignore`                         | Mis à jour                           |
| `README.md`                          | Mis à jour                           |
