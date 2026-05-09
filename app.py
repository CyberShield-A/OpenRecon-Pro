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
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SvelteKit compiled output (run: cd frontend && npm run build)
FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")

# Stockage temporaire des scans en cours et résultats
_scan_results: dict = {}
_scan_lock = threading.Lock()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_domain(raw: str) -> str:
    """Normalise une URL ou un domaine brut en domaine racine.

    Si l'entrée est un sous-domaine (ex: api.github.com), retourne le domaine
    enregistré (github.com). L'utilisateur n'a pas besoin de faire la distinction.
    """
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
    """Sert l'application SvelteKit (adapter-static).
    En développement, utilisez `npm run dev` dans frontend/ (Vite proxie /api).
    En production, compilez d'abord avec `npm run build`.
    """
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
    subdomain_input = bool(_ext.subdomain)  # True si api.github.com, False si github.com

    if mode not in ("NORMAL", "STEALTH", "AGGRESSIVE"):
        mode = "NORMAL"

    try:
        results = run(target=target, mode=mode)

        # Taguer les résultats du domaine racine
        for sub in results.get("subdomains", []):
            sub.setdefault("scope", "root")

        # Si l'utilisateur avait entré un sous-domaine (ex: api.github.com),
        # lancer une énumération sur ce sous-domaine pour trouver ses propres fils
        # (ex: v1.api.github.com, staging.api.github.com...)
        if subdomain_input and _ext.subdomain and _ext.domain and _ext.suffix:
            original_sub = f"{_ext.subdomain}.{_ext.domain}.{_ext.suffix}"
            try:
                sub_data = deep_subdomain_scan(target=original_sub, mode=mode)
                existing = {s["subdomain"] for s in results["subdomains"]}
                for entry in sub_data.get("results", []):
                    entry["scope"] = "subscope"  # sous-sous-domaines
                    if entry["subdomain"] not in existing:
                        results["subdomains"].append(entry)
                        existing.add(entry["subdomain"])
                results["subscope_target"] = original_sub
            except Exception as sub_err:
                results["subscope_error"] = str(sub_err)

        # Ajout des métadonnées
        results["target"] = target
        results["target_input"] = raw_target.strip()
        results["subdomain_input"] = subdomain_input
        results["mode"] = mode
        results["scan_date"] = datetime.now().strftime("%d/%m/%Y à %H:%M")

        # Stockage pour le téléchargement ultérieur
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
        return jsonify({"error": "scan_id introuvable. Lancez d'abord un scan."}), 404

    target = results.get("target", "domaine inconnu")

    report_text = generate_report(
        target=target,
        results=results,
        user_role=user_role,
        scan_type=scan_type,
        model=model
    )

    if not report_text:
        return jsonify({"error": "Impossible de générer le rapport. Vérifiez qu'Ollama est lancé."}), 503

    # Mise à jour du cache avec le rapport
    with _scan_lock:
        if scan_id in _scan_results:
            _scan_results[scan_id]["report"] = report_text
            _scan_results[scan_id]["report_role"] = user_role

    return jsonify({"report": report_text, "role": user_role})


# ─── API Parent Domain ────────────────────────────────────────────────────────

@app.route("/api/parent-domain", methods=["POST"])
def api_parent_domain():
    """Retrouve le domaine parent depuis un sous-domaine."""
    data = request.get_json(silent=True) or {}
    subdomain = data.get("subdomain", "").strip()

    if not subdomain:
        return jsonify({"error": "Le champ 'subdomain' est requis."}), 400

    subdomain = _clean_domain(subdomain)
    result = find_parent_domain(subdomain)

    return jsonify(result)


# ─── API Téléchargement ───────────────────────────────────────────────────────

@app.route("/api/download/<scan_id>/<fmt>", methods=["GET"])
def api_download(scan_id: str, fmt: str):
    """
    Télécharge les résultats du scan dans le format demandé.
    Formats supportés : json | txt | html | csv
    """
    with _scan_lock:
        results = _scan_results.get(scan_id)

    if not results:
        return jsonify({"error": "scan_id introuvable."}), 404

    target = results.get("target", "scan")
    safe_target = target.replace(".", "_")
    fmt = fmt.lower()

    if fmt == "json":
        filename = f"openrecon_{safe_target}.json"
        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        return send_file(tmp_path, as_attachment=True, download_name=filename,
                         mimetype="application/json")

    elif fmt == "txt":
        filename = f"openrecon_{safe_target}.txt"
        tmp_path = f"/tmp/{filename}"
        content = _results_to_txt(results)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(tmp_path, as_attachment=True, download_name=filename,
                         mimetype="text/plain")

    elif fmt == "html":
        filename = f"openrecon_{safe_target}.html"
        tmp_path = f"/tmp/{filename}"
        report_text = results.get("report", "")
        if not report_text:
            report_text = _results_to_txt(results)
        html = export_html_string(report_text, target)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html)
        return send_file(tmp_path, as_attachment=True, download_name=filename,
                         mimetype="text/html")

    elif fmt == "pdf":
        # PDF du rapport IA (texte narratif généré par Ollama)
        filename = f"openrecon_{safe_target}_rapport.pdf"
        report_text = results.get("report", "")
        if not report_text:
            return jsonify({"error": "Aucun rapport IA disponible. Générez d'abord le rapport."}), 400
        user_role = results.get("report_role", "")
        html = export_pdf_html_string(report_text, target, user_role=user_role)
        try:
            from weasyprint import HTML as WeasyprintHTML
            pdf_bytes = WeasyprintHTML(string=html).write_pdf()
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )
        except Exception as e:
            return jsonify({"error": f"Erreur génération PDF : {e}"}), 500

    elif fmt == "scan-pdf":
        # PDF structuré des données brutes du scan (sous-domaines, WHOIS, headers, techs)
        filename = f"openrecon_{safe_target}_analyse.pdf"
        html = _results_to_scan_pdf_html(results)
        try:
            from weasyprint import HTML as WeasyprintHTML
            pdf_bytes = WeasyprintHTML(string=html).write_pdf()
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )
        except Exception as e:
            return jsonify({"error": f"Erreur génération PDF : {e}"}), 500

    elif fmt == "csv":
        filename = f"openrecon_{safe_target}_subdomains.csv"
        tmp_path = f"/tmp/{filename}"
        content = _subdomains_to_csv(results)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(tmp_path, as_attachment=True, download_name=filename,
                         mimetype="text/csv")

    else:
        return jsonify({"error": f"Format '{fmt}' non supporté. Utilisez : json, txt, html, csv"}), 400


# ─── Helpers de conversion ────────────────────────────────────────────────────

def _results_to_scan_pdf_html(results: dict) -> str:
    """Génère un HTML professionnel (fond blanc, A4) pour l'export PDF des données brutes."""
    from datetime import datetime as _dt
    target     = results.get("target", "N/A")
    mode       = results.get("mode", "N/A")
    scan_date  = results.get("scan_date", _dt.now().strftime("%d/%m/%Y à %H:%M"))
    subdomains = results.get("subdomains", [])
    cdn_waf    = results.get("cdn_waf", {})
    wildcard   = results.get("wildcard", "N/A")
    whois      = results.get("whois", {})
    sec        = results.get("security_headers", {})
    techs      = results.get("technologies", {})

    css = (
        "@page{size:A4;margin:2.5cm 3cm}"
        "body{background:white;color:#1a1a1a;font-family:Arial,Helvetica,sans-serif;"
        "font-size:11pt;line-height:1.6;margin:0;padding:0}"
        ".header{border-bottom:3px solid #1e3a8a;padding-bottom:16px;margin-bottom:24px}"
        ".header h1{color:#1e3a8a;font-size:20pt;font-weight:700;margin:0 0 4px}"
        ".header .meta{color:#374151;font-size:10pt}"
        "h2{color:#1e3a8a;font-size:13pt;font-weight:700;"
        "border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:22px 0 10px}"
        "table{width:100%;border-collapse:collapse;margin:10px 0;font-size:10pt}"
        "th{background:#1e3a8a;color:white;padding:6px 10px;text-align:left;font-weight:600}"
        "td{padding:5px 10px;border-bottom:1px solid #e2e8f0;color:#1a1a1a;vertical-align:top}"
        "tr:nth-child(even) td{background:#f8fafc}"
        ".badge-ok{color:#065f46;font-weight:600}"
        ".badge-warn{color:#92400e;font-weight:600}"
        ".badge-bad{color:#991b1b;font-weight:600}"
        ".kv{display:flex;gap:8px;margin:4px 0}"
        ".kv .k{color:#475569;min-width:160px;font-size:10pt}"
        ".kv .v{color:#1a1a1a;font-size:10pt}"
        ".footer{border-top:1px solid #cbd5e1;padding-top:10px;margin-top:40px;"
        "color:#64748b;font-size:9pt;text-align:center}"
    )

    # ── En-tête ──
    html = (
        f"<!DOCTYPE html><html lang='fr'><head><meta charset='UTF-8'>"
        f"<title>Analyse – {target}</title><style>{css}</style></head><body>"
        f"<div class='header'><h1>OpenRecon Pro — Analyse de sécurité</h1>"
        f"<div class='meta'>Cible&nbsp;: <strong>{target}</strong>&ensp;·&ensp;"
        f"Mode&nbsp;: {mode}&ensp;·&ensp;{scan_date}</div></div>"
    )

    # ── Sous-domaines ──
    html += f"<h2>Sous-domaines découverts ({len(subdomains)})</h2>"
    if subdomains:
        html += "<table><tr><th>Sous-domaine</th><th>IPs</th><th>Confiance</th><th>Sources</th></tr>"
        for s in sorted(subdomains, key=lambda x: -x.get("confidence", 0)):
            conf = s.get("confidence", 0)
            cls  = "badge-ok" if conf >= 70 else ("badge-warn" if conf >= 40 else "badge-bad")
            ips  = ", ".join(s.get("ips", []))
            srcs = ", ".join(s.get("sources", []))
            html += (f"<tr><td>{s.get('subdomain','')}</td>"
                     f"<td>{ips}</td>"
                     f"<td class='{cls}'>{conf}%</td>"
                     f"<td>{srcs}</td></tr>")
        html += "</table>"
    else:
        html += "<p>Aucun sous-domaine trouvé.</p>"

    # ── WAF / CDN ──
    html += "<h2>Protection réseau</h2>"
    cdn = cdn_waf.get("cdn", "Aucun") if isinstance(cdn_waf, dict) else str(cdn_waf)
    waf = cdn_waf.get("waf", "Aucun") if isinstance(cdn_waf, dict) else "—"
    method = cdn_waf.get("method", "—") if isinstance(cdn_waf, dict) else "—"
    html += (f"<div class='kv'><span class='k'>CDN&nbsp;:</span><span class='v'>{cdn}</span></div>"
             f"<div class='kv'><span class='k'>WAF&nbsp;:</span><span class='v'>{waf}</span></div>"
             f"<div class='kv'><span class='k'>Méthode de détection&nbsp;:</span><span class='v'>{method}</span></div>"
             f"<div class='kv'><span class='k'>Wildcard DNS&nbsp;:</span><span class='v'>{wildcard}</span></div>")

    # ── WHOIS / RDAP ──
    if whois:
        html += "<h2>WHOIS / RDAP</h2>"
        skip = {"ip_addresses", "privacy_protected"}
        for k, v in whois.items():
            if k in skip or not v:
                continue
            label = k.replace("_", " ").capitalize()
            html += f"<div class='kv'><span class='k'>{label}&nbsp;:</span><span class='v'>{v}</span></div>"

    # ── En-têtes de sécurité ──
    score = sec.get("score")
    grade = sec.get("grade", "")
    if score is not None:
        html += f"<h2>En-têtes de sécurité HTTP — Score&nbsp;: {score}/100 ({grade})</h2>"
        present = sec.get("present", {})
        missing = sec.get("missing", {})
        html += "<table><tr><th>En-tête</th><th>Statut</th><th>Valeur / Impact</th></tr>"
        for h, d in present.items():
            warn = "⚠ " + d.get("warning","") if d.get("warning") else ""
            cls  = "badge-warn" if warn else "badge-ok"
            val  = str(d.get("value",""))[:80]
            html += f"<tr><td>{h}</td><td class='{cls}'>{'⚠ Avertissement' if warn else '✓ Présent'}</td><td>{val}{' — '+warn if warn else ''}</td></tr>"
        for h, d in missing.items():
            html += f"<tr><td>{h}</td><td class='badge-bad'>✗ Absent</td><td>{d.get('impact','')}</td></tr>"
        html += "</table>"

    # ── Technologies ──
    tech_list = techs.get("technologies", []) if isinstance(techs, dict) else []
    if tech_list:
        html += f"<h2>Technologies détectées ({len(tech_list)})</h2>"
        html += "<table><tr><th>Technologie</th><th>Version</th></tr>"
        for t in tech_list:
            if isinstance(t, dict):
                name = t.get("name", str(t))
                ver  = t.get("version") or "—"
            else:
                name, ver = str(t), "—"
            html += f"<tr><td>{name}</td><td>{ver}</td></tr>"
        html += "</table>"

    html += "<div class='footer'>Généré par OpenRecon Pro — Document confidentiel</div>"
    html += "</body></html>"
    return html


def _results_to_txt(results: dict) -> str:
    """Convertit les résultats du scan en rapport texte brut."""
    lines = [
        "=" * 60,
        f"OPENRECON PRO — RAPPORT DE SCAN",
        f"Cible     : {results.get('target', 'N/A')}",
        f"Mode      : {results.get('mode', 'N/A')}",
        f"Date      : {results.get('scan_date', 'N/A')}",
        "=" * 60,
        "",
        "--- SOUS-DOMAINES DÉCOUVERTS ---",
    ]
    for s in results.get("subdomains", []):
        ips = ", ".join(s.get("ips", []))
        lines.append(f"  {s.get('subdomain', '?')}  [{ips}]  conf={s.get('confidence', 0)}%")

    lines += [
        "",
        f"WAF / CDN    : {results.get('cdn_waf', 'N/A')}",
        f"Wildcard DNS : {results.get('wildcard', 'N/A')}",
        "",
        "--- WHOIS / RDAP ---",
    ]
    whois = results.get("whois", {})
    for k, v in whois.items():
        lines.append(f"  {k}: {v}")

    lines += [
        "",
        "--- EN-TÊTES DE SÉCURITÉ HTTP ---",
        f"  Score : {results.get('security_headers', {}).get('score', 'N/A')}%",
    ]
    missing = results.get("security_headers", {}).get("missing", {})
    for h, d in missing.items():
        lines.append(f"  ❌ {h} — {d.get('risk', '')} — {d.get('impact', '')}")

    lines += [
        "",
        "--- TECHNOLOGIES DÉTECTÉES ---",
    ]
    for t in results.get("technologies", {}).get("technologies", []):
        lines.append(f"  - {t}")

    if results.get("report"):
        lines += [
            "",
            "=" * 60,
            "RAPPORT IA",
            "=" * 60,
            results["report"],
        ]

    return "\n".join(lines)


def _subdomains_to_csv(results: dict) -> str:
    """Exporte les sous-domaines en CSV."""
    lines = ["subdomain,ips,confidence"]
    for s in results.get("subdomains", []):
        ips = " | ".join(s.get("ips", []))
        lines.append(f"{s.get('subdomain', '')},{ips},{s.get('confidence', 0)}")
    return "\n".join(lines)


# ─── Point d'entrée ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug = get("FLASK_DEBUG", "false").lower() == "true"
    port = int(get("PORT", "6000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
