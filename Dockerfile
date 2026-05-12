# Étape de build pour récupérer le dossier build du frontend
FROM python:3.10-slim

# 1. Installation des dépendances système (Les moteurs)
RUN apt-get update && apt-get install -y \
    nmap \
    whois \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Installation des libs Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Mise à jour forcée des bases de données de reco
RUN python3 -m webtech --update || true

# 4. Copie du code et du frontend buildé par Jenkins
COPY . .
# S'assure que Flask pourra servir les fichiers statiques
COPY --from=0 /app/frontend/build ./frontend/build 2>/dev/null || true

EXPOSE 5000

CMD ["python3", "app.py"]
