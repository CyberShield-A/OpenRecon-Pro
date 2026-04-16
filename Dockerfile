FROM python:3.10-slim

WORKDIR /app

# On installe les dépendances séparément (très bien)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie d'abord le reste du projet
COPY . .

# ASTUCE : On force la copie du fichier gui.py à la fin 
# pour s'assurer que Docker détecte sa modification
COPY gui.py /app/gui.py

EXPOSE 5000

# Utilise -u pour forcer Python à envoyer les logs en temps réel dans Jenkins
CMD ["python", "-u", "gui.py"]
