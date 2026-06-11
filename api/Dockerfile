FROM python:3.11-slim

WORKDIR /app

# Installera systemberoenden som kan behövas för t.ex. psycopg2 (Postgres-driver)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiera requirements och installera python-paket
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera resten av koden (används främst i produktion, i dev skrivs detta över av docker-compose-volymen)
COPY . .

EXPOSE 8000

# Starta Uvicorn med reload aktiverat för utveckling, och lyssna på alla gränssnitt (0.0.0.0)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]