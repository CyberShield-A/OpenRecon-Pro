FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .

# On augmente les retries et on donne un timeout très large (1000s = ~16 min)
# On utilise python -m pip pour être sûr d'utiliser le bon exécutable
RUN python -m pip install --upgrade pip --retries 10 --timeout 60 && \
    python -m pip install --no-cache-dir --retries 10 --default-timeout=1000 -r requirements.txt

COPY . .
COPY gui.py . 

EXPOSE 5000
CMD ["python", "-u", "gui.py"]
