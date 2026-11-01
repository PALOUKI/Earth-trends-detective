# Project progress

Updated: 2026-11-01

## Current milestone: M2 — regional analysis and trend statistics

- [x] Read the full `AGENT_BRIEF.md`; section 1 bis governs scope and sequencing.
- [x] Confirmed the GISTEMP v4 download page and selected gridded NetCDF product are published by NASA GISS. The official compressed file URL is `https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz`.
- [x] Added pinned Python dependencies, `uv`, Make targets, CI, and secret-safe environment template.
- [x] `uv sync --all-groups` succeeds with Python 3.11; pytest and Ruff pass locally.
- [x] Earthdata environment login succeeded and a live CMR search request completed; CMR returned zero GISTEMP records, consistent with GISTEMP being served directly by NASA GISS and not cataloged here as a CMR granule product.
- [ ] Deployment server/domain credentials are not available; M8 deployment cannot be completed until an endpoint and deployment access are available.

## Decisions and blockers

- MVP stays on GISTEMP only until M8, as required by the prioritized brief.
- The project runtime is pinned to Python 3.11 (supported range 3.11–3.12); the current shell has Python 3.13, outside that project range.
- NASA's current GISTEMP page exposes both a 2°×2° monthly anomaly NetCDF and compressed Zarr v3. The chosen source URL is the official NetCDF link; the live file has been downloaded and inspected.
- No product `short_name` will be recorded for GISTEMP because it is retrieved from the official GISS public download, not CMR.

## Completed: M1 — GISTEMP ingest and preprocessing

- [x] Downloaded the live NASA GISS GISTEMP v4 LOTI/ERSSTv5 1200 km monthly anomaly NetCDF gzip (24.6 MB compressed). Raw source stays under the ignored `data/raw/` directory.
- [x] Inspected source metadata: `tempanomaly`, units K, `time=1761` (1880-01 to 2026-09), native dimensions `lat=90`, `lon=180`, coordinates centered on 2° cells.
- [x] Implemented `make ingest` / `make preprocess`: converts time to month starts, normalizes longitude to [-180, 180], masks cells with <70% valid months or <120 months, saves `n_valid`, and writes chunked Zarr v2 with source/version/DOI/CRS attributes.
- [x] Opened the generated Zarr with xarray in the schema test; all tests pass.
- [ ] M1 acceptance check for independently reproduced global weighted GISTEMP curve and trend remains for M3 scientific validation.

## M0 acceptance summary

- Setup and tests pass locally after pinning Python 3.11, pandas, and stable Zarr 2.18.7 (Zarr 3 caused an async open deadlock in this environment).
- Earthdata login criterion passed. `make setup && make test` passes locally; a minimal lint/test GitHub Actions workflow is configured.

## Upcoming milestones

Next: M2 regional analyses and trend methods; M3 scientific validation; M4 map layers; M5 API; M6 web MVP; M8 deploy. M7 remains deferred until after M8.
