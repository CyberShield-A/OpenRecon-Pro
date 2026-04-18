FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# On s'assure que gui.py est bien là
COPY gui.py . 
EXPOSE 5000
CMD ["python", "-u", "gui.py"]
