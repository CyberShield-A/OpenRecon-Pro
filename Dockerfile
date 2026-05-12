FROM python:3.10-slim

# 1. Installation des outils système (moteurs)
RUN apt-get update && apt-get install -y \
    nmap \
    whois \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Initialisation des outils
RUN python3 -m webtech --update || true

# 4. Copie de TOUT le projet (incluant le build frontend déjà fait par Jenkins)
COPY . .

EXPOSE 5000

CMD ["python3", "app.py"]
