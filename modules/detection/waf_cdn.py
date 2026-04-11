import requests
import secrets

CDN_PATTERNS = {
    "Cloudflare": ["cloudflare", "cf-ray"],
    "Akamai": ["akamai"],
    "Fastly": ["fastly"],
    "CloudFront": ["cloudfront"],
    "Imperva": ["imperva"],
    "Sucuri": ["sucuri"]
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def random_user_agent():
    return secrets.choice(USER_AGENTS)

def detect_cdn_waf(subdomain):

    result = {
        "cdn": None,
        "waf": None
    }

    try:
        r = requests.get(
            f"http://{subdomain}",
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": random_user_agent()}
        )

        headers = str(r.headers).lower()

        for provider, patterns in CDN_PATTERNS.items():
            for pattern in patterns:
                if pattern in headers:
                    result["cdn"] = provider
                    result["waf"] = provider + " WAF"

    except requests.RequestException:
        pass

    return result