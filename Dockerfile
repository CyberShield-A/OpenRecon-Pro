# ... (début identique)
FROM python:3.10-slim
WORKDIR /app

# Installation des libs pour PDF + Outils de diagnostic réseau
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    nmap \
    whois \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*
# ... (reste identique)
