# Earth Trends Detective

An educational, reproducible tool for investigating linear changes in NASA Earth science data. The current MVP uses NASA GISS GISTEMP v4 monthly surface temperature anomalies on a 2° grid. It connects a selected region to its time series, estimates a linear trend, and reports statistical uncertainty in plain language.

**Data access:** NASA GISS publishes the selected public GISTEMP gridded NetCDF at [its data downloads page](https://data.giss.nasa.gov/gistemp/data_v4.html). Dataset attribution and access details are recorded in the application and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## Local setup

Requires Python 3.11 or 3.12, `uv`, and (for deployment) Docker Compose.

```sh
make setup
make ingest
make test
cd web && npm ci
```

Then start `make dev` in one terminal and `cd web && npm run dev` in another. The API runs at `http://localhost:8000`; Vite serves the frontend at `http://localhost:5173` and proxies `/api` and `/tiles` requests to it. Run `make build` for a production frontend build. Web dependencies are pinned in `web/package.json` and `web/package-lock.json`.

See [docs/PROGRESS.md](docs/PROGRESS.md) for milestone status and known access needs.

## Résumé français

Détective des tendances du système terrestre est un outil pédagogique et reproductible. Le MVP commence par les anomalies mensuelles de température de surface NASA GISS GISTEMP v4 sur une grille de 2°. Il reliera une région choisie à sa série temporelle, estimera une tendance et présentera l’incertitude statistique en langage clair.
