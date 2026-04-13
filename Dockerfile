# Utilise une image Python stable
FROM python:3.10-slim

# Empêche Python de générer des fichiers .pyc et force l'affichage des logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Dossier de travail dans le conteneur
WORKDIR /app

# Installation des outils système nécessaires (Cyber & Recon)
RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste du code source
COPY . .

# Port interne de l'application (Flask utilise souvent 5000)
EXPOSE 5000

# Commande de lancement
CMD ["python", "recon.py"]
