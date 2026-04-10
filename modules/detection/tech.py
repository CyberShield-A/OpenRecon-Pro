# modules/detection/tech.py
import re
import requests
from utils.logger import loading, info, warning

# Signatures de technologies détectables via headers et HTML
TECH_SIGNATURES = {
    "headers": {
        "X-Powered-By": {
            "PHP": ["php"],
            "ASP.NET": ["asp.net"],
            "Express.js": ["express"],
            "Next.js": ["next.js"],
        },
        "Server": {
            "Apache": ["apache"],
            "Nginx": ["nginx"],
            "IIS": ["microsoft-iis"],
            "LiteSpeed": ["litespeed"],
            "Caddy": ["caddy"],
        },
        "X-Generator": {
            "WordPress": ["wordpress"],
            "Drupal": ["drupal"],
            "Joomla": ["joomla"],
        }
    },
    "html_patterns": {
        "WordPress": [r'wp-content/', r'wp-includes/', r'<meta name="generator" content="WordPress'],
        "Drupal": [r'Drupal\.settings', r'sites/default/files', r'<meta name="generator" content="Drupal'],
        "Joomla": [r'/media/jui/', r'<meta name="generator" content="Joomla'],
        "Shopify": [r'cdn\.shopify\.com', r'Shopify\.theme'],
        "React": [r'react\.production\.min\.js', r'_reactRootContainer', r'__NEXT_DATA__'],
        "Vue.js": [r'vue\.runtime', r'v-cloak', r'data-v-[a-f0-9]'],
        "Angular": [r'ng-version', r'angular\.min\.js'],
        "jQuery": [r'jquery[.-][\d.]+\.min\.js'],
        "Bootstrap": [r'bootstrap[.-][\d.]*\.min\.(css|js)'],
        "Google Analytics": [r'google-analytics\.com/analytics', r'gtag/js\?id='],
        "Google Tag Manager": [r'googletagmanager\.com/gtm'],
    },
    "cookie_patterns": {
        "PHP": ["PHPSESSID"],
        "ASP.NET": ["ASP.NET_SessionId"],
        "Java (JSP)": ["JSESSIONID"],
        "Laravel": ["laravel_session"],
        "Django": ["csrftoken", "sessionid"],
    }
}


def detect_technologies(domain):
    """
    Identifie les technologies utilisées par un site via les headers HTTP,
    le contenu HTML et les cookies.
    """
    loading(f"Détection des technologies pour {domain}...")

    result = {
        "server": None,
        "technologies": [],  # Liste de noms de technos détectées
        "details": {}        # techno -> source de détection
    }

    try:
        r = requests.get(
            f"https://{domain}",
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )

        headers = r.headers
        html = r.text
        cookies = r.cookies

        detected = {}

        # 1. Détection via headers
        for header_name, techs in TECH_SIGNATURES["headers"].items():
            header_val = headers.get(header_name, "").lower()
            if header_val:
                for tech_name, patterns in techs.items():
                    for pattern in patterns:
                        if pattern in header_val:
                            detected[tech_name] = f"Header {header_name}: {headers.get(header_name)}"

        # Serveur web
        server = headers.get("Server", "")
        if server:
            result["server"] = server

        # 2. Détection via HTML
        for tech_name, patterns in TECH_SIGNATURES["html_patterns"].items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    detected[tech_name] = "Détecté dans le code source"
                    break

        # 3. Détection via cookies
        cookie_names = [c.name for c in cookies]
        for tech_name, patterns in TECH_SIGNATURES["cookie_patterns"].items():
            for pattern in patterns:
                if pattern in cookie_names:
                    detected[tech_name] = f"Cookie: {pattern}"
                    break

        result["technologies"] = sorted(detected.keys())
        result["details"] = detected

        if detected:
            info(f"Technologies détectées : {', '.join(result['technologies'])}")
        else:
            info("Aucune technologie identifiée.")

    except requests.RequestException as e:
        warning(f"Impossible d'analyser les technologies de {domain} : {e}")

    return result
