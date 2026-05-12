# --- STAGE 1: Frontend ---
FROM node:20-slim AS build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --quiet
COPY frontend/ ./
RUN npm run build

# --- STAGE 2: Security App ---
FROM python:3.10-slim
WORKDIR /app

# Installation des outils de reconnaissance (Nmap, Whois, etc.) + Libs PDF
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    nmap \
    whois \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Fix pour WEBTECH : création du dossier pour la base de données
RUN mkdir -p /root/.local/share/webtech

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .
# Importation du build Svelte/Frontend
COPY --from=build-frontend /app/frontend/build ./frontend/build

EXPOSE 5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# CORRECTION : Utilisation de la méthode .update() au lieu de .update_database()
# Cela permet de télécharger les signatures Wappalyzer pour détecter les technos (WordPress, etc.)
RUN python3 -c "import webtech; w=webtech.WebTech(); w.update()" || true

CMD ["python", "app.py"]
