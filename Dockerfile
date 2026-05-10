# --- ÉTAPE 1 : Build du Frontend SvelteKit ---
FROM node:20-slim AS build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- ÉTAPE 2 : Image Finale (Backend Python) ---
FROM python:3.10-slim
WORKDIR /app

# Dépendances système (PDF & Scan)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir --retries 10 --default-timeout=1000 -r requirements.txt

# Copie de l'intégralité du projet
COPY . .
COPY --from=build-frontend /app/frontend/build ./frontend/build

# --- AJOUT CRITIQUE POUR FORCER LE PORT ---
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Commande modifiée pour forcer l'écoute sur 0.0.0.0
CMD ["python", "-m", "flask", "run"]
