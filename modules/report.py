# modules/report.py
import json
from datetime import datetime
from utils.logger import info, warning, success
from utils.config import get

# Modèle Ollama chargé depuis .env (clé OLLAMA_MODEL), défini côté backend uniquement
OLLAMA_MODEL = get("OLLAMA_MODEL", "llama3.1:8b")

def build_prompt(target, results):
    """Construit le prompt pour Ollama à partir de TOUS les résultats du scan."""
    subdomains = results.get("subdomains", [])
    cdn_waf = results.get("cdn_waf", "Aucun")
    wildcard = results.get("wildcard", "Désactivé")
    whois_data = results.get("whois", {})
    headers_data = results.get("security_headers", {})
    tech_data = results.get("technologies", {})

    # --- Section sous-domaines ---
    sub_details = ""
    for s in subdomains:
        name = s.get("subdomain", "?")
        ips = ", ".join(s.get("ips", []))
        conf = s.get("confidence", 0)
        sub_details += f"  - {name} (IPs: {ips}, Confiance: {conf}%)\n"
    if not sub_details:
        sub_details = "  Aucun sous-domaine découvert.\n"

    # --- Section RDAP ---
    whois_section = "Non disponible"
    if whois_data and whois_data.get("registrar"):
        whois_section = f"""  Registrar : {whois_data.get('registrar', 'Inconnu')}
  Propriétaire : {whois_data.get('registrant', 'Non disponible')}
  Date de création : {whois_data.get('creation_date', 'Inconnue')}
  Date d'expiration : {whois_data.get('expiration_date', 'Inconnue')}
  Serveurs DNS : {', '.join(whois_data.get('name_servers', [])) or 'N/A'}
  Emails exposés : {', '.join(whois_data.get('emails', [])) or 'Aucun'}
  Protection vie privée : {'Oui' if whois_data.get('privacy') else 'Non — les informations du propriétaire sont PUBLIQUES'}
  DNSSEC : {whois_data.get('dnssec', 'Inconnu')}"""

    # --- Section headers de sécurité ---
    headers_section = "Non analysé"
    if headers_data and (headers_data.get("present") or headers_data.get("missing")):
        present_list = "\n".join([f"    ✅ {h} : {v}" for h, v in headers_data.get("present", {}).items()]) or "    Aucun"
        missing_list = ""
        for h, details in headers_data.get("missing", {}).items():
            missing_list += f"    ❌ {h} — Risque: {details['risk']} — {details['impact']}\n"
        if not missing_list:
            missing_list = "    Tous les en-têtes critiques sont présents."

        headers_section = f"""  Score de sécurité : {headers_data.get('score', 0)}% (Grade: {headers_data.get('grade', 'N/A')})
  Serveur : {headers_data.get('server', 'Non identifié')}
  
  En-têtes présents :
{present_list}
  
  En-têtes MANQUANTS (vulnérabilités) :
{missing_list}"""

    # --- Section technologies ---
    tech_section = "Non analysé"
    if tech_data:
        techs = tech_data.get("technologies", [])
        if techs:
            tech_lines = ""
            for t in techs:
                source = tech_data.get("details", {}).get(t, "")
                tech_lines += f"  - {t} ({source})\n"
            tech_section = f"""  Serveur web : {tech_data.get('server', 'Non identifié')}
  Technologies détectées :
{tech_lines}"""
        else:
            tech_section = "  Aucune technologie identifiée avec certitude."

    prompt = f"""Tu es un expert senior en cybersécurité mandaté pour auditer le domaine "{target}". Tu rédiges un rapport de reconnaissance passive destiné à des décideurs et du personnel NON technique. Ton rapport doit être professionnel mais accessible.

=============================================
   RÉSULTATS COMPLETS DU SCAN DE RECONNAISSANCE
=============================================

🎯 CIBLE : {target}
📅 Date du scan : {datetime.now().strftime('%d/%m/%Y à %H:%M')}

--- 1. SOUS-DOMAINES DÉCOUVERTS ({len(subdomains)} trouvés) ---
{sub_details}
Protection WAF/CDN détectée : {cdn_waf}
DNS Wildcard : {wildcard}

--- 2. INFORMATIONS RDAP (Carte d'identité du domaine) ---
{whois_section}

--- 3. EN-TÊTES DE SÉCURITÉ HTTP ---
{headers_section}

--- 4. TECHNOLOGIES DÉTECTÉES ---
{tech_section}

=============================================
   FIN DES RÉSULTATS
=============================================

INSTRUCTIONS DE RÉDACTION — À SUIVRE OBLIGATOIREMENT :

Rédige le rapport en français en suivant EXACTEMENT cette structure :

## 1. RÉSUMÉ EXÉCUTIF
En 3-4 phrases maximum, explique ce qui a été analysé et les conclusions principales. Utilise des analogies concrètes. Par exemple : "Un sous-domaine, c'est comme une porte d'un bâtiment — chaque porte ouverte et non surveillée est un point d'entrée potentiel."

## 2. CE QUE NOUS AVONS DÉCOUVERT

### 2.1 Surface d'exposition (sous-domaines)
- Combien de "portes" avons-nous trouvé ?
- Lesquelles semblent sensibles (admin, staging, dev, vpn, internal) ?
- Est-ce que le domaine a une protection WAF/CDN ? Explique ce que ça signifie concrètement.

### 2.2 Carte d'identité du domaine (RDAP)
- Le domaine expire-t-il bientôt ? (Si < 90 jours, c'est un risque)
- Les informations du propriétaire sont-elles exposées publiquement ?
- Les emails trouvés peuvent-ils être utilisés pour du phishing ?

### 2.3 Protection du site web (en-têtes de sécurité)
- Quel est le score de sécurité et qu'est-ce que ça veut dire concrètement ?
- Pour CHAQUE en-tête manquant, explique le risque en langage simple avec une analogie.

### 2.4 Technologies utilisées
- Quelles technologies ont été identifiées ?
- Y a-t-il des technologies obsolètes ou connues pour avoir des failles ?

## 3. ÉVALUATION DU RISQUE
Donne un niveau global : 🟢 Faible / 🟡 Moyen / 🟠 Élevé / 🔴 Critique
Justifie en 2-3 phrases.

## 4. PLAN D'ACTION (par priorité)
Liste numérotée des actions de remédiation. Pour CHAQUE action :
- **Quoi** : description simple de l'action
- **Pourquoi** : quel risque ça élimine
- **Qui doit le faire** : équipe technique, administrateur, direction
- **Urgence** : Immédiate / Court terme / Moyen terme

## 5. PROCHAINES ÉTAPES
3 à 5 recommandations concrètes pour la suite.

RÈGLES DE RÉDACTION :
- JAMAIS de jargon technique sans explication entre parenthèses
- Utilise des analogies du quotidien (porte, serrure, carte d'identité, etc.)
- Sois factuel : base-toi UNIQUEMENT sur les données fournies, n'invente rien
- Le rapport doit être compréhensible par un dirigeant d'entreprise sans bagage technique
- Sois concis mais complet
"""
    return prompt


def generate_report(target, results, model=None):
    if model is None:
        model = OLLAMA_MODEL
    """
    Génère un rapport via Ollama.
    Retourne le texte du rapport ou None en cas d'erreur.
    """
    try:
        import ollama
    except ImportError:
        warning("Le package 'ollama' n'est pas installé. Installez-le avec : pip install ollama")
        return None

    prompt = build_prompt(target, results)

    info(f"Génération du rapport IA avec le modèle '{model}'...")
    info("Cela peut prendre quelques instants...")

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un analyste senior en cybersécurité. "
                        "Tu rédiges des rapports d'audit de reconnaissance passive. "
                        "Tes rapports sont destinés à des personnes NON techniques (dirigeants, managers, RH). "
                        "Tu utilises un langage clair, des analogies concrètes, et tu évites le jargon. "
                        "Tu te bases UNIQUEMENT sur les données fournies — tu n'inventes jamais de failles ou de risques. "
                        "Tu réponds toujours en français."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        report_text = response["message"]["content"]
        success("Rapport IA généré avec succès.")
        return report_text

    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            warning("Impossible de se connecter à Ollama. Vérifiez qu'Ollama est lancé (commande: ollama serve).")
        elif "not found" in error_msg.lower() or "model" in error_msg.lower():
            warning(f"Le modèle '{model}' n'est pas disponible. Téléchargez-le avec : ollama pull {model}")
        else:
            warning(f"Erreur lors de la génération du rapport : {error_msg}")
        return None


def save_report(report_text, filepath):
    """Sauvegarde le rapport dans un fichier texte."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        success(f"Rapport sauvegardé dans : {filepath}")
    except IOError as e:
        warning(f"Impossible de sauvegarder le rapport : {e}")


def export_html(report_text, target, filepath):
    """Exporte le rapport IA en fichier HTML stylisé et partageable."""
    try:
        import re as _re

        # Conversion Markdown basique -> HTML
        html_body = report_text
        # Headers
        html_body = _re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=_re.MULTILINE)
        html_body = _re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=_re.MULTILINE)
        # Bold
        html_body = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
        # Lists
        html_body = _re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=_re.MULTILINE)
        # Emojis de risque en badges
        html_body = html_body.replace('🟢', '<span class="badge green">🟢')
        html_body = html_body.replace('🟡', '<span class="badge yellow">🟡')
        html_body = html_body.replace('🟠', '<span class="badge orange">🟠')
        html_body = html_body.replace('🔴', '<span class="badge red">🔴')
        # Paragraphes
        html_body = html_body.replace('\n\n', '</p><p>')
        html_body = f"<p>{html_body}</p>"

        date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport OpenRecon Pro — {target}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a; color: #e2e8f0;
            line-height: 1.7; padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155; border-radius: 12px;
            padding: 30px; margin-bottom: 30px; text-align: center;
        }}
        .header h1 {{ color: #3b82f6; font-size: 28px; margin-bottom: 8px; }}
        .header .meta {{ color: #94a3b8; font-size: 14px; }}
        .content {{
            background: #1e293b; border: 1px solid #334155;
            border-radius: 12px; padding: 30px;
        }}
        h2 {{ color: #3b82f6; margin: 25px 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid #334155; font-size: 20px; }}
        h3 {{ color: #60a5fa; margin: 18px 0 8px 0; font-size: 16px; }}
        p {{ margin: 8px 0; }}
        li {{ margin: 4px 0 4px 20px; }}
        strong {{ color: #f1f5f9; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-weight: bold; }}
        .badge.green {{ background: #166534; color: #4ade80; }}
        .badge.yellow {{ background: #854d0e; color: #facc15; }}
        .badge.orange {{ background: #9a3412; color: #fb923c; }}
        .badge.red {{ background: #991b1b; color: #f87171; }}
        .footer {{
            text-align: center; margin-top: 30px;
            color: #64748b; font-size: 12px;
        }}
        @media print {{
            body {{ background: white; color: #1e293b; padding: 20px; }}
            .header {{ background: #f1f5f9; border-color: #cbd5e1; }}
            .header h1 {{ color: #1e40af; }}
            .content {{ background: white; border-color: #cbd5e1; }}
            h2 {{ color: #1e40af; border-color: #cbd5e1; }}
            h3 {{ color: #2563eb; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔎 OPENRECON PRO</h1>
            <div class="meta">
                Rapport d'audit de reconnaissance passive<br>
                Cible : <strong>{target}</strong> — {date_str}
            </div>
        </div>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            Généré par OpenRecon Pro — Rapport confidentiel
        </div>
    </div>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        success(f"Rapport HTML exporté dans : {filepath}")
        return True

    except Exception as e:
        warning(f"Impossible d'exporter le rapport HTML : {e}")
        return False
        warning(f"Impossible de sauvegarder le rapport : {e}")
