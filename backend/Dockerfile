# Runtime image for the Raspberry Pi (arm64). python:3.11-slim is multi-arch,
# so the SAME Dockerfile builds natively on the Pi or cross-builds via buildx.
# NO headless browser here — the scraper uses httpx + selectolax only.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# selectolax/httpx ship arm64 wheels, so no compiler toolchain is needed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Run as non-root.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
