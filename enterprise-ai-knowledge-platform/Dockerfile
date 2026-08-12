FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[api]"

# Copy application code
COPY src/ src/
COPY config/ config/

# Environment
ENV ENVIRONMENT=prod
ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health')"

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
