# Production image: gunicorn + WhiteNoise. Build: docker build -t tunehub .
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PRIVATE_MEDIA_ROOT=/data/private_media

WORKDIR /app

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/private_media \
    && chown -R app:app /data

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .

# Compile translations and collect static files at build time (no secrets needed).
RUN python scripts/build_translations.py \
    && DEBUG=False SECRET_KEY=build-only-not-secret python manage.py collectstatic --noinput

USER app
EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

ENTRYPOINT ["sh", "docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
