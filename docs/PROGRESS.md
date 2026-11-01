# Project progress

Updated: 2026-11-01

## Current milestone: M6 — frontend MVP

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
- [x] M1 curve/trend acceptance checked during M3 against NASA's published global monthly mean; numerical differences are documented below.

## Completed: M2 — regional analysis and trend statistics

- [x] Added cosine-latitude weighted regional mean extraction with explicit missing-cell handling and month-start period slicing.
- [x] Implemented monthly deseasonalization for display, OLS slope/95% CI/t test, Sen slope/95% CI, classic Mann-Kendall, and Hamed-Rao adjusted Mann-Kendall.
- [x] Added grid analysis using `xarray.apply_ufunc` with `dask='parallelized'`, Benjamini-Hochberg FDR (`alpha=0.10`), and {-1,0,1} sign classes.
- [x] Tests cover known AR(1) trend recovery, 1,000 reference comparisons against SciPy and pyMannKendall, missing/constant series, false-positive rate, FDR, seasonal removal, and area weighting.
- [x] Vectorized OLS/FDR map precalculation across all three windows took 52.84 seconds total on this machine (90×180 cells; 1880-2026 source). The detailed regional path still reports Sen and both Mann-Kendall tests.
- [ ] Full-grid per-pixel Sen/Hamed-Rao is not computed; those rigorous methods are run on the selected region to keep the global map responsive. This is documented in `docs/METHODS.md`.

## Completed: M3 — scientific validation (GISTEMP scope)

- [x] Compared 561 monthly global series (1980-01–2026-09) to the NASA GISS published global CSV: bias 0.00267 K, RMSE 0.05006 K, maximum absolute difference 0.18366 K.
- [x] Grid weighted and published global linear slopes agree to 0.0000008 K/year (0.0210564 vs 0.0210556 K/year).
- [x] Regional grid results show 0.06926 K/year for 70–90°N and 0.03408 K/year for 30–60°N, matching the published qualitative Arctic amplification pattern (England et al., 2021; DOI 10.1029/2021GL094086).
- [x] Reproducible code and the expected/obtained summary are in `notebooks/01_validation_gistemp.ipynb`; NASA source and access date are in `docs/DATA_SOURCES.md`.
- [ ] Giovanni cross-check was not completed: an interactive regional export for this GISTEMP product was not accessible in the run. No Giovanni values are claimed.

## Completed: M4 — map products and visual encoding

- [x] Generated OLS trend grids and Benjamini-Hochberg significance masks for `full`, `2010-fin`, and `2015-fin` from the actual GISTEMP Zarr.
- [x] Generated transparent world slope images and nonsignificant stipple overlays under `data/tiles/gistemp_tas_anom/`; these use the brief's accepted client-side image-overlay path in place of XYZ tiles.
- [x] Palette is diverging and centered on zero, with symmetric clipping at the 98th percentile of absolute slopes; layer metadata includes K/year, bounds, scale, and interpretation.
- [x] PNG encoding and layer rendering have fixture tests. Full-grid products were generated successfully for all three windows.
- [x] Full-grid OLS/FDR results are generated locally for all three windows but are not committed; reproducible generation is through `make trends && make tiles`.

## Completed: M5 — API

- [x] FastAPI routes are implemented for health, variables, suggestions, illustrative regions, regional analysis, point analysis, comparisons, trend metadata, and map images.
- [x] Deterministic summaries are provided in English and French; OpenAPI docs are available at `/docs`.
- [x] Async HTTP contract tests cover the catalog, health, map layers, regional analysis, and clicked point response.
- [x] Tests use `httpx` ASGI calls and synthetic fixture datasets; all API endpoint tests pass.
- [x] Warm GISTEMP point endpoint measured at 206–223 ms locally after an initial 575 ms cold call; the brief's <300 ms target is met after data/cache warm-up.
- [x] CORS defaults to the local frontend origin and is configurable by `ALLOWED_ORIGINS` for deployment.

## M0 acceptance summary

- Setup and tests pass locally after pinning Python 3.11, pandas, and stable Zarr 2.18.7 (Zarr 3 caused an async open deadlock in this environment).
- Earthdata login criterion passed. `make setup && make test` passes locally; a minimal lint/test GitHub Actions workflow is configured.

## Upcoming milestones

Next: M2 regional analyses and trend methods; M3 scientific validation; M4 map layers; M5 API; M6 web MVP; M8 deploy. M7 remains deferred until after M8.
