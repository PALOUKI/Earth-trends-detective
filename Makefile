.PHONY: setup ingest preprocess trends tiles test lint dev web-dev build deploy

TRENDS_FLAGS ?=

setup:
	uv sync --all-groups

ingest:
	uv run python -m pipeline.cli ingest gistemp_tas_anom

preprocess:
	uv run python -m pipeline.cli preprocess gistemp_tas_anom

trends:
	uv run python -m pipeline.cli trends gistemp_tas_anom $(TRENDS_FLAGS)

tiles:
	uv run python -m pipeline.cli tiles gistemp_tas_anom

test:
	uv run pytest

lint:
	uv run ruff check .

dev:
	uv run uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

web-dev:
	cd web && npm run dev

build:
	cd web && npm run build

deploy:
	./deploy/deploy.sh
