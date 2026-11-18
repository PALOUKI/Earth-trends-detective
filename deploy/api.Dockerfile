FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.11.1 \
    && uv sync --frozen --no-dev

COPY api ./api
COPY pipeline ./pipeline
COPY data/catalog.yaml ./data/catalog.yaml

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
