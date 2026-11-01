.PHONY: setup ingest preprocess trends tiles test lint dev web-dev build deploy

TRENDS_FLAGS ?=
VARIABLE ?= gistemp_tas_anom

setup:
	uv sync --all-groups

ingest:
	uv run python -m pipeline.cli ingest $(VARIABLE)

preprocess:
	uv run python -m pipeline.cli preprocess $(VARIABLE)

trends:
	uv run python -m pipeline.cli trends $(VARIABLE) $(TRENDS_FLAGS)

tiles:
	uv run python -m pipeline.cli tiles $(VARIABLE)

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
