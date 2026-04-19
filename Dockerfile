FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .

# Mise à jour de pip et augmentation du timeout pour les packages lourds
RUN pip install --upgrade pip && \
    pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .

# Note: COPY . . copie déjà tout, cette ligne est redondante mais inoffensive
COPY gui.py . 

EXPOSE 5000
CMD ["python", "-u", "gui.py"]
