# --- STAGE 1: Compilation du Frontend ---
FROM node:20-slim AS build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --quiet
COPY frontend/ ./
RUN npm run build

# --- STAGE 2: Image Finale de Sécurité ---
FROM python:3.10-slim
WORKDIR /app

# Installation des outils de reconnaissance (NMAP, WHOIS, DNS)
# Et des dépendances pour les rapports PDF (Pango/Cairo)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    # Outils indispensables pour un hacker/chercheur
    nmap \
    whois \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des bibliothèques Python (Flask, Ollama, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source et du frontend buildé
COPY . .
COPY --from=build-frontend /app/frontend/build ./frontend/build

# CRUCIAL : On s'assure que le port correspond à celui de ton Terraform
EXPOSE 5000

# Variables d'environnement
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Lancement avec binding obligatoire sur 0.0.0.0
CMD ["python", "app.py"]
