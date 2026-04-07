
# =============================================================================
FROM python:3.12-slim AS runtime
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=bank_management.settings.production
 
# Runtime-only system deps (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
 
# Non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser
 
# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
 
WORKDIR /app
 
# Copy project source
COPY --chown=appuser:appgroup . .
 
# Create directories for static files and logs
RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R appuser:appgroup /app
 
USER appuser
 
# Collect static files at build time
RUN python manage.py collectstatic --noinput
 
EXPOSE 8000
 
# Health check — hits the /health/ endpoint every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
 
# Entrypoint runs migrations then starts gunicorn
COPY --chown=appuser:appgroup docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
 
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "bank_management.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]