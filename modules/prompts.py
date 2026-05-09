"""
modules/prompts.py
──────────────────
Prompts centralisés pour la génération de rapports IA.
Chaque rôle utilisateur possède un prompt système et un template de rapport adapté.

Rôles disponibles :
  - etudiant        : rapport pédagogique, sans guide d'exploitation
  - chef_entreprise : rapport risques / impact business, langage non technique
  - pentester       : rapport technique détaillé, commandes d'exploitation
  - admin_systeme   : rapport axé exposition infrastructure & remédiation
  - developpeur     : rapport centré sur les en-têtes HTTP manquants & corrections
"""

from datetime import datetime


# ─── Profils utilisateurs ─────────────────────────────────────────────────────

USER_ROLES = {
    "etudiant": "Étudiant",
    "chef_entreprise": "Chef d'entreprise",
    "pentester": "Hacker / Pentester",
    "admin_systeme": "Administrateur système",
    "developpeur": "Développeur",
}

SCAN_TYPES = {
    "complet": "scan complet de reconnaissance",
    "subdomain": "scan de sous-domaines",
    "web": "scan web (en-têtes & technologies)",
    "vulnerabilite": "scan de vulnérabilités",
    "rdap": "lookup RDAP / WHOIS",
}


# ─── Blocs de données communs ─────────────────────────────────────────────────

def _build_data_block(target: str, results: dict, scan_type: str) -> str:
    """Construit le bloc de données brutes injecté dans tous les prompts."""
    subdomains = results.get("subdomains", [])
    cdn_waf = results.get("cdn_waf", "Aucun")
    wildcard = results.get("wildcard", "Désactivé")
    whois_data = results.get("whois", {})
    headers_data = results.get("security_headers", {})
    tech_data = results.get("technologies", {})

    # Sous-domaines
    sub_lines = ""
    for s in subdomains:
        name = s.get("subdomain", "?")
        ips = ", ".join(s.get("ips", []))
        conf = s.get("confidence", 0)
        sub_lines += f"  - {name}  [IPs: {ips}]  confiance: {conf}%\n"
    if not sub_lines:
        sub_lines = "  Aucun sous-domaine découvert.\n"

    # RDAP
    whois_section = "  Non disponible"
    if whois_data and whois_data.get("registrar"):
        whois_section = f"""  Registrar       : {whois_data.get('registrar', 'Inconnu')}
  Propriétaire    : {whois_data.get('registrant', 'Non disponible')}
  Création        : {whois_data.get('creation_date', 'Inconnue')}
  Expiration      : {whois_data.get('expiration_date', 'Inconnue')}
  Serveurs DNS    : {', '.join(whois_data.get('name_servers', [])) or 'N/A'}
  Emails exposés  : {', '.join(whois_data.get('emails', [])) or 'Aucun'}
  Vie privée      : {'Oui' if whois_data.get('privacy') else 'Non — informations du propriétaire PUBLIQUES'}
  DNSSEC          : {whois_data.get('dnssec', 'Inconnu')}"""

    # En-têtes HTTP
    if headers_data and (headers_data.get("present") or headers_data.get("missing")):
        present_list = "\n".join(
            [f"    ✅ {h}: {v}" for h, v in headers_data.get("present", {}).items()]
        ) or "    Aucun"
        missing_list = ""
        for h, details in headers_data.get("missing", {}).items():
            missing_list += f"    ❌ {h} — Risque: {details['risk']} — {details['impact']}\n"
        if not missing_list:
            missing_list = "    Tous les en-têtes critiques sont présents."
        headers_section = (
            f"  Score : {headers_data.get('score', 0)}%  (Grade: {headers_data.get('grade', 'N/A')})\n"
            f"  Serveur : {headers_data.get('server', 'Non identifié')}\n\n"
            f"  En-têtes PRÉSENTS :\n{present_list}\n\n"
            f"  En-têtes MANQUANTS :\n{missing_list}"
        )
    else:
        headers_section = "  Non analysé"

    # Technologies
    techs = tech_data.get("technologies", [])
    if techs:
        tech_section = f"  Serveur web : {tech_data.get('server', '?')}\n"
        for t in techs:
            src = tech_data.get("details", {}).get(t, "")
            tech_section += f"  - {t} ({src})\n"
    else:
        tech_section = "  Aucune technologie identifiée."

    return f"""=============================================
  RÉSULTATS DU {scan_type.upper()}
=============================================
🎯 CIBLE      : {target}
📅 DATE       : {datetime.now().strftime('%d/%m/%Y à %H:%M')}

--- SOUS-DOMAINES ({len(subdomains)} trouvés) ---
{sub_lines}
Protection WAF/CDN : {cdn_waf}
DNS Wildcard       : {wildcard}

--- RDAP / WHOIS ---
{whois_section}

--- EN-TÊTES DE SÉCURITÉ HTTP ---
{headers_section}

--- TECHNOLOGIES DÉTECTÉES ---
{tech_section}
============================================="""


# ─── Prompts par rôle ─────────────────────────────────────────────────────────

def get_system_prompt(user_role: str) -> str:
    """Retourne le prompt système adapté au rôle utilisateur."""

    prompts = {
        "etudiant": (
            "Tu es un assistant pédagogique spécialisé en cybersécurité. "
            "Tu expliques les résultats d'un scan de reconnaissance à un étudiant curieux. "
            "Ton rôle est d'enseigner et de faire comprendre, pas d'instruire sur l'exploitation. "
            "Tu utilises des exemples concrets et des analogies simples. "
            "Tu n'indiques JAMAIS comment exploiter une vulnérabilité — tu te contentes de l'expliquer. "
            "Tu réponds toujours en français, avec un ton bienveillant et pédagogique."
        ),
        "chef_entreprise": (
            "Tu es un consultant senior en cybersécurité présentant un rapport à un dirigeant d'entreprise. "
            "Tu évites tout jargon technique non expliqué. "
            "Tu te concentres sur les risques business : réputation, conformité, pertes financières potentielles. "
            "Les points critiques sont mis en évidence avec 🔴 CRITIQUE. "
            "Tu fournis des recommandations claires et priorisées, avec un niveau d'urgence. "
            "Tu réponds toujours en français, avec un ton professionnel et direct."
        ),
        "pentester": (
            "Tu es un expert en tests d'intrusion (pentesting) rédigeant un rapport technique. "
            "Tu fournis des détails techniques précis : CVE, vecteurs d'attaque, surface d'exposition. "
            "Pour chaque vulnérabilité identifiée, tu indiques les commandes de vérification "
            "(nmap, curl, dig, nuclei, etc.) et les méthodes d'exploitation connues. "
            "Tu couvres : reconnaissance, énumération, exploitation potentielle, persistance. "
            "Tu réponds toujours en français, avec un style technique concis."
        ),
        "admin_systeme": (
            "Tu es un architecte sécurité rédigeant un rapport pour un administrateur système. "
            "Tu te concentres sur l'exposition de l'infrastructure : sous-domaines exposés, DNS, WAF. "
            "Pour chaque problème identifié, tu expliques le risque lié et fournis "
            "les étapes concrètes pour masquer, protéger ou corriger le problème "
            "(configuration DNS, pare-feu, proxy inverse, etc.). "
            "Tu réponds toujours en français, avec un ton opérationnel et précis."
        ),
        "developpeur": (
            "Tu es un expert en sécurité applicative (AppSec) rédigeant un rapport pour un développeur. "
            "Tu te concentres principalement sur les en-têtes de sécurité HTTP manquants. "
            "Pour chaque en-tête absent, tu fournis : "
            "1) l'impact exact sur la sécurité, "
            "2) le code d'implémentation (nginx, Apache, Express, Django, etc.), "
            "3) la valeur recommandée selon les standards OWASP / Mozilla. "
            "Tu réponds toujours en français, avec un ton technique et pratique."
        ),
    }
    return prompts.get(user_role, prompts["chef_entreprise"])


def get_report_template(user_role: str) -> str:
    """Retourne les instructions de structure du rapport pour chaque rôle."""

    templates = {
        "etudiant": """
## Instructions de rédaction — Rapport Pédagogique

Rédige le rapport en français en suivant cette structure :

## 1. QU'EST-CE QUE CE SCAN A ANALYSÉ ?
Explique en termes simples ce qu'est la reconnaissance passive et pourquoi c'est important.

## 2. CE QUE NOUS AVONS TROUVÉ

### 2.1 Les sous-domaines
- Qu'est-ce qu'un sous-domaine ? (analogie simple)
- Combien en avons-nous trouvé et pourquoi est-ce important ?
- Explique ce que sont le WAF et le Wildcard DNS simplement.

### 2.2 Les informations d'enregistrement du domaine (RDAP)
- Qu'est-ce que le RDAP / WHOIS ?
- Quelles informations sont exposées et pourquoi c'est sensible ?

### 2.3 Les en-têtes de sécurité HTTP
- Qu'est-ce qu'un en-tête HTTP ? (analogie : règles de sécurité d'un bâtiment)
- Pour chaque en-tête manquant : explique ce que c'est et le risque potentiel, SANS indiquer comment l'exploiter.

### 2.4 Les technologies
- Quelles technologies ont été détectées ? Explique brièvement leur rôle.

## 3. RÉCAPITULATIF DES POINTS IMPORTANTS
3 à 5 points clés à retenir sous forme de liste.

## 4. POUR ALLER PLUS LOIN
Suggère des ressources ou thèmes d'apprentissage liés aux découvertes.

Règles : sois pédagogique, utilise des analogies, ne fournis JAMAIS d'instructions d'exploitation.
""",

        "chef_entreprise": """
## Instructions de rédaction — Rapport Dirigeant

Rédige le rapport en français en suivant cette structure :

## 1. RÉSUMÉ EXÉCUTIF
En 4 phrases maximum : ce qui a été analysé et les conclusions principales.
Utilise des analogies concrètes (porte, serrure, carte d'identité…).

## 2. ÉTAT DES LIEUX

### 2.1 Exposition du domaine (sous-domaines)
- Combien de "portes d'entrée" ont été identifiées ?
- Y a-t-il des portes sensibles (admin, staging, dev, vpn) ?
- Le site est-il protégé par un WAF/CDN ? Expliquer concrètement.

### 2.2 Informations publiques sur la société
- Quelles informations sont accessibles publiquement ?
- Risques de phishing ou d'usurpation d'identité ?

### 2.3 Protection du site web
- Score de sécurité global et signification.
- Pour chaque protection manquante : quel est le risque business concret ?
- 🔴 CRITIQUE / 🟠 ÉLEVÉ / 🟡 MOYEN selon la gravité.

### 2.4 Technologies exposées
- Quelles technologies sont visibles ? Risque d'obsolescence ?

## 3. ÉVALUATION GLOBALE DU RISQUE
Niveau : 🟢 Faible / 🟡 Moyen / 🟠 Élevé / 🔴 Critique — avec justification en 2-3 phrases.

## 4. PLAN D'ACTION PRIORITAIRE
Liste numérotée. Pour chaque action :
- **Quoi** : description simple
- **Pourquoi** : quel risque ça élimine
- **Qui** : équipe technique / administrateur / direction
- **Urgence** : Immédiate / Court terme / Moyen terme

## 5. PROCHAINES ÉTAPES
3 recommandations concrètes pour la suite.

Règles : JAMAIS de jargon sans explication, analogies du quotidien, factuel uniquement.
""",

        "pentester": """
## Instructions de rédaction — Rapport Pentest

Rédige le rapport en français en suivant cette structure :

## 1. EXECUTIVE SUMMARY
Résumé de la surface d'attaque identifiée.

## 2. SURFACE D'ATTAQUE

### 2.1 Énumération des sous-domaines
- Liste complète avec IPs, score de confiance.
- Sous-domaines à fort intérêt (admin, staging, dev, api, vpn, internal…).
- Commandes de vérification : `dig`, `nslookup`, `dnsx`.

### 2.2 Infrastructure & WAF
- Protection WAF/CDN détectée et techniques de contournement potentielles.
- DNS Wildcard : implications pour le fuzzing.

### 2.3 Informations RDAP
- Emails exposés utilisables pour du spear-phishing ou OSINT.
- Dates d'expiration : risque de domain hijacking.

### 2.4 En-têtes de sécurité HTTP (vecteurs d'attaque)
Pour chaque en-tête manquant :
- Vecteur d'attaque activé (XSS, clickjacking, MITM…)
- Commande de vérification : `curl -I https://target.com`
- Payload / méthode d'exploitation type.

### 2.5 Technologies — CVE & versions
- Versions identifiées et CVE associées connues.
- Vecteurs d'exploitation liés aux technologies détectées.

## 3. CHAÎNE D'ATTAQUE POTENTIELLE
Décris un scénario d'attaque réaliste basé sur les données collectées.

## 4. RECOMMANDATIONS TECHNIQUES
Corrections précises, par ordre de criticité.

Règles : sois précis et technique, base-toi uniquement sur les données fournies.
""",

        "admin_systeme": """
## Instructions de rédaction — Rapport Administrateur Système

Rédige le rapport en français en suivant cette structure :

## 1. SYNTHÈSE — EXPOSITION INFRASTRUCTURE
Résumé de l'exposition réseau et des risques opérationnels.

## 2. ANALYSE DE L'EXPOSITION

### 2.1 Sous-domaines exposés
- Liste des sous-domaines découverts avec leurs IPs.
- Sous-domaines critiques à restreindre ou masquer.
- Risques liés à l'exposition de chacun.

### 2.2 Configuration DNS
- DNS Wildcard activé : risques et comment le désactiver.
- Serveurs DNS exposés : recommandations DNSSEC.

### 2.3 WAF / CDN
- Protection en place ou absence.
- Recommandations : Cloudflare, AWS Shield, etc.

### 2.4 En-têtes de sécurité HTTP
- Manques identifiés et configuration serveur recommandée.
- Exemples de configuration : nginx / Apache / HAProxy.

### 2.5 Technologies & stack technique
- Technologies exposées et risques de version obsolète.

## 3. PLAN DE REMÉDIATION
Actions classées par priorité :
- **Priorité 1 — Immédiat** : actions à réaliser sous 24h
- **Priorité 2 — Court terme** : sous 7 jours
- **Priorité 3 — Moyen terme** : sous 30 jours

Pour chaque action : commande ou configuration précise.

## 4. SURVEILLANCE RECOMMANDÉE
Outils et métriques à mettre en place pour surveiller l'infrastructure.

Règles : sois opérationnel, fournis des exemples de commandes et configurations.
""",

        "developpeur": """
## Instructions de rédaction — Rapport Développeur

Rédige le rapport en français en suivant cette structure :

## 1. RÉSUMÉ — SÉCURITÉ APPLICATIVE
Résumé rapide des problèmes de sécurité HTTP détectés.

## 2. AUDIT DES EN-TÊTES DE SÉCURITÉ HTTP

Pour chaque en-tête manquant, fournis une section structurée comme suit :

### [Nom de l'en-tête]
- **Statut** : ❌ Absent
- **Impact** : quel type d'attaque cet en-tête prévient-il ? (XSS, clickjacking, MIME sniffing…)
- **Valeur recommandée** : `valeur exacte recommandée`
- **Implémentation** :
  - Nginx : `add_header NomHeader "valeur";`
  - Apache : `Header always set NomHeader "valeur"`
  - Express.js : `res.setHeader('NomHeader', 'valeur')` ou via helmet.js
  - Django : `SECURE_HEADER_NAME = True` (si applicable)
- **Référence** : lien OWASP ou Mozilla Observatory

Pour chaque en-tête présent : confirmer la valeur et signaler si elle peut être améliorée.

## 3. TECHNOLOGIES IDENTIFIÉES
- Technologies exposées : risques de version visible.
- Recommandation : masquer les versions dans les en-têtes serveur.

## 4. CHECKLIST DE SÉCURITÉ HTTP
Tableau récapitulatif : [ ✅ / ❌ ] pour chaque en-tête standard OWASP.

## 5. RESSOURCES
- OWASP Secure Headers Project
- Mozilla Observatory
- helmet.js (Node.js), django-csp (Django), secureheaders (Rails)

Règles : sois précis, fournis du code prêt à l'emploi, référence les standards OWASP.
""",
    }
    return templates.get(user_role, templates["chef_entreprise"])


def build_full_prompt(target: str, results: dict, user_role: str, scan_type: str) -> str:
    """
    Construit le prompt utilisateur complet :
    données du scan + instructions de rapport selon le rôle.
    """
    scan_label = SCAN_TYPES.get(scan_type, scan_type)
    data_block = _build_data_block(target, results, scan_label)
    template = get_report_template(user_role)
    role_label = USER_ROLES.get(user_role, user_role)

    return f"""Voici les résultats d'un {scan_label} effectué sur le domaine "{target}".
Tu dois générer un rapport adapté au profil : {role_label}.

{data_block}

{template}
"""
