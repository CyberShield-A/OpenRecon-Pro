# --- ÉTAPE 1 : Build du Frontend SvelteKit ---
FROM node:20-slim AS build-frontend
WORKDIR /app/frontend

# Empêche Node de saturer la RAM de ta VM
ENV NODE_OPTIONS="--max-old-space-size=512"

# Installation des dépendances
COPY frontend/package*.json ./
RUN npm ci --quiet

# Copie du code source frontend
COPY frontend/ ./

# Génération des fichiers SvelteKit et Build final
# On utilise npx pour forcer la synchronisation des types/fichiers
RUN npx svelte-kit sync && npm run build

# --- ÉTAPE 2 : Image Finale (Backend Python) ---
FROM python:3.10-slim
WORKDIR /app

# Installation des dépendances système critiques (PDF & Scan)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Gestion des dépendances Python (ton requirements.txt)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir --retries 10 --default-timeout=1000 -r requirements.txt

# Copie de l'intégralité du projet (Backend, core, modules, etc.)
COPY . .

# Injection du frontend compilé dans le dossier attendu par Flask
COPY --from=build-frontend /app/frontend/build ./frontend/build

# --- CONFIGURATION DE FORÇAGE FLASK ---
# Pour s'assurer que Flask écoute bien Terraform sur le port 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Commande de lancement (le flag -u pour les logs en temps réel dans Jenkins)
CMD ["python", "-m", "flask", "run"]
