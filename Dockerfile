FROM python:3.11-slim

# tesseract-ocr : moteur d'OCR utilise par app/ocr.py (appele en ligne de
# commande, pas de dependance Python supplementaire).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# /data est le volume persistant fourni par le superviseur Home Assistant
# pour chaque add-on : la base SQLite et les photos y vivent, et
# survivent aux mises a jour/redemarrages de l'add-on.
VOLUME ["/data"]

EXPOSE 8000
CMD ["/run.sh"]
