FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY alembic.ini .
COPY ./alembic ./alembic
COPY seed.sql .

RUN mkdir -p /app/uploads

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && PGPASSWORD=$DB_PASSWORD psql -h db -U $DB_USER -d $DB_NAME -f /app/seed.sql 2>/dev/null || true && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
