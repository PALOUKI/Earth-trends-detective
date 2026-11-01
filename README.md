# Earth Trends Detective

An educational, reproducible tool for investigating linear changes in NASA Earth science data. The first milestone focuses on NASA GISS GISTEMP v4 monthly surface temperature anomalies on a 2° grid. It will connect a selected region to its time series, estimate a trend, and report statistical uncertainty in plain language.

**Data access:** NASA GISS publishes the selected public GISTEMP gridded NetCDF at [its data downloads page](https://data.giss.nasa.gov/gistemp/data_v4.html). Dataset attribution and access date will be recorded in the application and `docs/DATA_SOURCES.md` after ingestion is implemented.

## Local setup

Requires Python 3.11 or 3.12, `uv`, and (for deployment) Docker Compose.

```sh
make setup
make test
make dev
cd web && npm install
cd web && npm run dev
```

The API runs at `http://localhost:8000`; Vite serves the frontend at `http://localhost:5173` and proxies `/api` requests to the API. Run `make build` for a production frontend build. Direct web dependency versions are pinned. The npm lockfile is pending registry access and must be generated before a production build.

See [docs/PROGRESS.md](docs/PROGRESS.md) for milestone status and known access needs.

## Résumé français

Détective des tendances du système terrestre est un outil pédagogique et reproductible. Le MVP commence par les anomalies mensuelles de température de surface NASA GISS GISTEMP v4 sur une grille de 2°. Il reliera une région choisie à sa série temporelle, estimera une tendance et présentera l’incertitude statistique en langage clair.
