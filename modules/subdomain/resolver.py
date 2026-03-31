import dns.resolver
import dns.exception

# Configuration du résolveur pour la rapidité
resolver = dns.resolver.Resolver()
resolver.timeout = 1
resolver.lifetime = 1

def resolve_domain(domain):
    """
    Tente de résoudre un domaine en adresses IPv4 (A).
    Retourne une liste d'IPs ou une liste vide en cas d'échec.
    """
    try:
        answers = resolver.resolve(domain, "A")
        return [rdata.to_text() for rdata in answers]
    except (dns.resolver.NXDOMAIN, 
            dns.resolver.NoAnswer, 
            dns.resolver.Timeout, 
            dns.exception.DNSException):
        return []