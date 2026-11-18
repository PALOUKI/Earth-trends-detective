# Earth Trends Detective

**Explore where Earth science variables are changing, how quickly they are changing, and whether their trends are statistically significant.**

Earth Trends Detective is an educational web application for exploring NASA Earth observation and model data. Select an available variable, a region, and a time window to inspect a deseasonalized time series, estimate its trend, review statistical tests, and compare spatial patterns on a map.

The application is designed to make the analysis traceable: data products and their source metadata are catalogued, processing is reproducible, and products are exposed for analysis only when their required data and derived outputs are present.

## What the application does

- Offers an English/French interface, a variable catalogue, and a guided investigation workflow.
- Lets users choose a predefined region or draw a rectangular area on the map; clicked map locations can also be analyzed.
- Displays monthly regional series, seasonal adjustment, fitted trend, confidence intervals, and statistical results.
- Provides global trend tiles over a NASA GIBS Blue Marble basemap, with controls for layer visibility and trend-layer opacity.
- Summarizes the variable, region, trend rate, and significance in plain language, with caveats about interpretation.
- Supports regional comparison and data/map exports through the API.
- Provides a direct CUAHSI station search, retrieval, and monthly trend analysis by selected region and measurement. Giovanni, NASA Hydrology Time Series, AppEEARS, and NOAA CDO are linked as acquisition tools, with a CSV import fallback for downloaded series.

### Data availability

Availability is determined by the processed data installed with the application, not by the presence of a catalogue entry alone. The current local catalogue marks eight variables as analysis-ready: GISTEMP temperature anomaly, MODIS NDVI and EVI, GPM IMERG precipitation, MERRA-2 evaporation, GLDAS topsoil moisture, AIRS surface atmospheric temperature, and OMI tropospheric NO₂. Their local coverage periods and product identifiers are listed in [`docs/NASA_RESOURCES_FOR_SUBMISSION.md`](docs/NASA_RESOURCES_FOR_SUBMISSION.md) and [`data/catalog.yaml`](data/catalog.yaml). Check [`docs/PROGRESS.md`](docs/PROGRESS.md) for current validation and deployment status.

## Analysis at a glance

Regional values use cosine-of-latitude area weighting over the selected rectangular region. The analysis removes the monthly seasonal cycle before fitting trends. The base results include an ordinary least-squares slope, its 95% confidence interval and t-test, plus Sen's slope and Mann–Kendall results. The application also exposes autocorrelation-adjusted Hamed–Rao statistics and map-wide Benjamini–Hochberg false-discovery-rate results where those products are available. These methods describe statistical patterns; they do not identify causes.

See [`docs/METHODS.md`](docs/METHODS.md) for assumptions and limitations, and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for dataset attribution, versions, DOIs, access details, and processing notes.

## Repository architecture

| Path | Responsibility |
| --- | --- |
| `api/app/` | FastAPI application, request/response schemas, and deterministic bilingual summaries. |
| `api/tests/` | API endpoint, export, health, and summary contract tests. |
| `pipeline/ingest/` | Dataset-specific acquisition and decoding adapters for GISTEMP, MODIS, GPM, AIRS, OMI, and monthly NetCDF products. |
| `pipeline/trends/` | Regional and grid trend statistics, annual analysis, breakpoint calculations, and derived exports. |
| `pipeline/tiling/` | Rendering of analytical raster products as map tiles. |
| `pipeline/cli.py` | Command-line orchestration for ingest, preprocessing, trend calculation, and tile generation. |
| `pipeline/regions.py`, `pipeline/variables.py` | Shared region handling and variable/product configuration. |
| `pipeline/tests/` | Ingestion, region, statistical, rendering, and tile tests. |
| `data/catalog.yaml` | Curated product definitions, source identifiers, units, descriptions, periods, and integration states. |
| `data/raw/` | Downloaded source files; local data, excluded from version control. |
| `data/processed/` | Processed chunked datasets and derived raster products; generated locally and excluded from version control. |
| `data/tiles/` | Generated XYZ map tiles served by the API/deployment; excluded from version control. |
| `web/src/` | Vue 3 application, map and chart interface, API client, shared utilities, and frontend tests. |
| `notebooks/` | Reproducible validation notebooks, including comparison with published GISTEMP data. |
| `docs/` | Methods, data provenance, milestone progress, and project documentation. |
| `deploy/` | API/web container definitions, Caddy configuration, and remote deployment script. |
| `docker-compose.yml` | Local/remote service topology for the API, static frontend, and HTTPS proxy. |
| `AGENT_BRIEF.md` | Full challenge requirements and project acceptance criteria. |

## Technology

- **Data and API:** Python 3.11–3.12, `uv`, xarray, Dask, Zarr, NumPy, SciPy, Numba, FastAPI, and Pydantic.
- **Web client:** Vue 3, Vite, TypeScript, MapLibre GL JS, and Apache ECharts.
- **Maps:** NASA GIBS Blue Marble for geographic context; analytical trend and significance layers are generated from the selected science dataset.
- **Deployment:** Docker Compose and Caddy for HTTPS termination and static asset/API routing.

## Requirements

- Python 3.11 or 3.12 and [`uv`](https://docs.astral.sh/uv/).
- Node.js and npm versions compatible with the constraints in [`web/package.json`](web/package.json).
- Earthdata credentials and any required NASA data access authorization for products that need authenticated acquisition. NASA GISTEMP's public download does not require Earthdata credentials.
- Docker Compose and server/DNS/SSH access only for deployment.

## Setup and run locally

From the repository root:

```sh
make setup
make test
cd web && npm ci
```

The first command installs the pinned Python environment. `make test` runs the Python test suite. `npm ci` installs the pinned frontend dependencies.

Start the backend in one terminal from the repository root:

```sh
make dev
```

Start the frontend in a second terminal:

```sh
cd web
npm run dev
```

Open the URL printed by Vite, normally **http://localhost:5173**. The API is available at **http://localhost:8000** and the interactive API documentation at **http://localhost:8000/docs**. Vite proxies API and tile requests to the local backend.

### Run the services manually

If you prefer not to use the Make target, start the API from the repository root:

```sh
.venv/bin/uvicorn api.app.main:app --host 0.0.0.0 --port 8000
```

Then start the frontend in another terminal using the commands above.

## Data processing commands

The standard pipeline is run one product at a time. Product IDs are defined in `data/catalog.yaml`.

```sh
make ingest VARIABLE=gistemp_tas_anom
make preprocess VARIABLE=gistemp_tas_anom
make trends VARIABLE=gistemp_tas_anom
make tiles VARIABLE=gistemp_tas_anom
```

For an Earthdata-backed product, replace the ID with an available product, for example `modis_ndvi` or `gpm_precipitation`. Some NASA services require Earthdata credentials and approval for the relevant application. Configure credentials in a local `.env` file or the supported Earthdata credential store; never commit secrets. See `.env.example` and the product-specific adapter before starting a long acquisition.

Useful quality commands:

```sh
make test                 # Python tests
make lint                 # Ruff checks
cd web && npm test        # Frontend unit tests
cd web && npm run build   # Type-check and production build
```

## Deployment

The repository includes a Docker Compose deployment using FastAPI, a built static frontend, and Caddy. Deployment requires a reachable server, SSH access, a DNS name, and inbound ports 80 and 443. Configure the environment variables consumed by `deploy/deploy.sh` (`DEPLOY_HOST`, `DEPLOY_USER`, optional `DEPLOY_SSH_KEY`, and `SITE_DOMAIN`), then run:

```sh
make deploy
```

The script transfers derived products required by the application rather than raw NASA downloads or local secrets. Review [`docs/PROGRESS.md`](docs/PROGRESS.md) for current deployment prerequisites and acceptance status.

When a host Nginx server already owns ports 80 and 443, run the stack with `docker compose -f docker-compose.yml -f deploy/docker-compose.nginx.yml up --build -d` instead. This binds the Caddy gateway to `127.0.0.1:18081` in HTTP-only mode; configure the host Nginx virtual host and Certbot certificate to serve the public HTTPS domain and proxy requests to that local port. This avoids stopping Nginx or disturbing its other sites.

## Documentation

- [`AGENT_BRIEF.md`](AGENT_BRIEF.md): challenge scope and acceptance criteria.
- [`docs/METHODS.md`](docs/METHODS.md): statistical methods, assumptions, and interpretation limits.
- [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md): NASA product sources, identifiers, DOIs, and processing provenance.
- [`docs/PROGRESS.md`](docs/PROGRESS.md): implementation status, validation evidence, and outstanding work.
- [`notebooks/01_validation_gistemp.ipynb`](notebooks/01_validation_gistemp.ipynb): GISTEMP validation workflow.

## Project status

This project is under active development. Product availability, validation coverage, and deployment status can change as acquisition and acceptance work proceeds. The progress log and live catalogue are the source of truth for current state. Statistical association is not causal attribution, and results depend on the selected product, region, time window, data coverage, and test assumptions.

## License

Project-authored source code and documentation are licensed under the [MIT License](LICENSE), copyright © 2026 Earth Trend Detective contributors. NASA datasets and imagery, map data, fonts, and other third-party materials are not relicensed by this notice; their respective terms apply. See [`docs/NASA_RESOURCES_FOR_SUBMISSION.md`](docs/NASA_RESOURCES_FOR_SUBMISSION.md) and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for source details.

## Project summary

Earth Trends Detective is an educational application for investigating trends in NASA Earth science data. Users choose an analysis-ready variable, a region, and a time period, then view a deseasonalized time series, an estimated rate of change, confidence intervals, and statistical tests. A map shows where trends occur and whether they are statistically significant. Data sources, methods, and limitations are documented; statistical results do not identify causes.

To get started, run `make setup`, then `make dev` from the repository root and `npm run dev` from `web/`. The sections above and linked documents describe the architecture, processing commands, tests, data sources, and methods.
