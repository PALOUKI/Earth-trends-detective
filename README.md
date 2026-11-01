# Earth Trends Detective

An educational, reproducible tool for investigating linear changes across NASA Earth science variables. GISTEMP is the first analysis-ready variable. The catalog also tracks verified MODIS vegetation indices and precipitation, soil-water, atmospheric-temperature, and air-quality products with explicit availability states. A product is selectable for analysis only after its real time series and trend maps have been processed. MOD13C2 NDVI/EVI ingestion is being completed; GES DISC products await Earthdata application authorization.

**Data access:** NASA GISS publishes the selected public GISTEMP gridded NetCDF at [its data downloads page](https://data.giss.nasa.gov/gistemp/data_v4.html). Dataset attribution and access details are recorded in the application and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## Local setup

Requires Python 3.11 or 3.12, `uv`, and (for deployment) Docker Compose.

```sh
make setup
make ingest
make test
cd web && npm ci
```

Select another pipeline by id, for example `make ingest VARIABLE=modis_ndvi`, then
`make trends VARIABLE=modis_ndvi` and `make tiles VARIABLE=modis_ndvi`. MODIS
ingest requires Earthdata credentials; variables blocked by a NASA service
agreement are listed in the catalog but do not run until real access is available.

Then start `make dev` in one terminal and `cd web && npm run dev` in another. The API runs at `http://localhost:8000`; Vite serves the frontend at `http://localhost:5173` and proxies `/api` and `/tiles` requests to it. Run `make build` for a production frontend build. Web dependencies are pinned in `web/package.json` and `web/package-lock.json`.

See [docs/PROGRESS.md](docs/PROGRESS.md) for milestone status and known access needs.

## Remote deployment

After generating all selected variables' trend products and map tiles, configure a host with Docker Compose, SSH access, a public DNS name pointed at it, and inbound ports 80/443 open. Then deploy with:

```sh
export DEPLOY_HOST=your-server.example
export DEPLOY_USER=your-ssh-user
export DEPLOY_SSH_KEY="$HOME/.ssh/id_ed25519"  # omit when your SSH agent is configured
export SITE_DOMAIN=your-public-domain.example
make deploy
```

The deployment script transfers processed Zarr, trend COGs, and XYZ map tiles for all selected variables; it excludes raw NASA downloads and `.env`. It builds and starts the Compose services remotely and checks `https://<SITE_DOMAIN>/api/health`.

## Résumé français

Détective des tendances du système terrestre est un outil pédagogique et reproductible pour analyser plusieurs variables NASA. GISTEMP est la première variable disponible ; MODIS NDVI/EVI est en cours d'intégration et les autres produits vérifiés sont listés avec leur état d'accès et de traitement. Une variable n'est activée qu'après l'ingestion réelle et la génération des analyses et cartes.
