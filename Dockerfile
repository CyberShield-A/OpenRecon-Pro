# --- STAGE 1: Frontend Build ---
FROM node:20-slim AS build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --quiet
COPY frontend/ ./
RUN npm run build

# --- STAGE 2: Backend & Runner ---
FROM python:3.10-slim
WORKDIR /app

# Outils indispensables pour engine.py
RUN apt-get update && apt-get install -y \
    nmap whois dnsutils curl \
    && rm -rf /var/lib/apt/lists/*

# Fix Database Webtech
RUN mkdir -p /root/.local/share/webtech

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# On récupère le build du stage 1
COPY --from=build-frontend /app/frontend/build ./frontend/build

# Variables pour que webtech et nmap fonctionnent
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

# Mise à jour des bases de signatures au build
RUN python3 -m webtech --update || true

EXPOSE 5000

# On lance directement app.py qui sert tout
CMD ["python", "app.py"]
