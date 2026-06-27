FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Settings.py imports DATABASES/SECRET_KEY at module load time, before
# collectstatic ever touches the database - these placeholders only need
# to satisfy that import for this build step. Render's real env vars
# override them at container start, so nothing here reaches production.
RUN SECRET_KEY=build-time-placeholder \
    DATABASE_URL=postgresql://user:password@localhost:5432/placeholder \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Render injects $PORT and requires the app to bind to it; falls back to
# 8000 for local `docker run` / docker-compose where $PORT is unset.
CMD ["sh", "-c", "gunicorn tradecycle.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
