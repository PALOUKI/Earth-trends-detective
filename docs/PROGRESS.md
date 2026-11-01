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

## M2 — regional analysis and trend statistics (partial)

- [x] Added cosine-latitude weighted regional mean extraction with explicit missing-cell handling and month-start period slicing.
- [x] Implemented monthly deseasonalization for display, OLS slope/95% CI/t test, Sen slope/95% CI, classic Mann-Kendall, and Hamed-Rao adjusted Mann-Kendall.
- [x] Added Dask-backed `xarray.apply_ufunc` OLS map analysis and Benjamini-Hochberg FDR (`alpha=0.10`).
- [ ] The brief's per-pixel grid output requires Sen, classic Mann-Kendall, Hamed-Rao, and the specified `numba @njit(parallel=True)` implementation; the current map only calculates OLS and FDR. M2 is therefore not accepted.
- [ ] The required `--annual` robustness option, full output Zarr variables, false-positive simulation, and specified full-grid performance measurement are not implemented/verified.

## M3 — scientific validation (partial)

- [x] Compared 561 monthly global series (1980-01–2026-09) to the NASA GISS published global CSV: bias 0.00267 K, RMSE 0.05006 K, maximum absolute difference 0.18366 K.
- [x] Grid weighted and published global linear slopes agree to 0.0000008 K/year (0.0210564 vs 0.0210556 K/year).
- [x] Regional grid results show 0.06926 K/year for 70–90°N and 0.03408 K/year for 30–60°N, matching the published qualitative Arctic amplification pattern (England et al., 2021; DOI 10.1029/2021GL094086).
- [x] Reproducible code and the expected/obtained summary are in `notebooks/01_validation_gistemp.ipynb`; NASA source and access date are in `docs/DATA_SOURCES.md`.
- [ ] Live [Giovanni no-script catalog](https://giovanni.gsfc.nasa.gov/giovanni/daac-bin/noscript.cgi) checked on 2026-11-01; an exact `GISTEMP` search returned no result. Since section 2 requires one GISTEMP variable until deployment, no different dataset was substituted. Giovanni validation is blocked by the absence of the selected product and M3 is not accepted.

## M4 — map products and visual encoding (XYZ generation implemented; depends on incomplete M2 map statistics)

- [x] Generated OLS trend grids and Benjamini-Hochberg significance masks for `full`, `2010-fin`, and `2015-fin` from the actual GISTEMP Zarr.
- [x] Replaced the earlier single-image overlay (which did not meet the brief) with pinned `rio-tiler==9.4.9` raster XYZ tiles for the slope and nonsignificance stipple layers, zooms 0–5.
- [x] Tile files are laid out under `data/tiles/<id>/<window>/<layer>/{z}/{x}/{y}.png`; `/api/trend` returns tile URL templates, and Caddy serves tiles with long cache headers.
- [x] Palette is diverging and centered on zero, with symmetric clipping at the 98th percentile of absolute slopes; layer metadata includes K/year, bounds, scale, and interpretation.
- [x] Tests verify XYZ paths, palette metadata, zoom bounds, and tile serving. Full XYZ layers were generated for all three windows from the current OLS/FDR data.
- [ ] The map's statistical layers still depend on M2's OLS/FDR-only output; rerun after the required per-pixel base/rigorous outputs are implemented.

## M5 — API (partial)

- [x] FastAPI routes are implemented for health, variables, suggestions, regions, regional analysis, point analysis, comparisons, trend metadata, and XYZ tiles.
- [x] Added `GET /api/export`: regional monthly series as CSV and precomputed map layers as PNG.
- [x] Added Pydantic response models for variables, analyses, comparisons, and map metadata.
- [x] Added Pydantic response models to the region and point endpoints.
- [ ] Broader contract checks against every field and behavior required by section 12 remain; M5 is not accepted yet.
- [ ] The required regional on-demand rupture result is missing.
- [x] Deterministic summaries are provided in English and French; OpenAPI docs are available at `/docs`.
- [x] Async HTTP contract tests cover the catalog, health, map layers, regional analysis, and clicked point response.
- [x] Tests use `httpx` ASGI calls and synthetic fixture datasets; all API endpoint tests pass.
- [x] Warm GISTEMP point endpoint measured at 206–223 ms locally after an initial 575 ms cold call; the brief's <300 ms target is met after data/cache warm-up.
- [x] CORS defaults to the local frontend origin and is configurable by `ALLOWED_ORIGINS` for deployment.

## M6 — frontend MVP (partial; manual and acceptance review outstanding)

- [x] Reviewed the supplied Stitch design system and explorer, wizard, and demo screens. Applied the NASA-blue palette, Inter typography, 8px spacing rhythm, analytical side panel, map workspace, and three-step investigation wizard.
- [x] Implemented Vue 3 + Vite + TypeScript UI with MapLibre, ECharts, English default/French switch, region controls, rectangle drawing, period presets, point clicks, bilingual summaries, methods, and two GISTEMP guided examples as required for M6.
- [x] Map background now uses NASA GIBS via its official MapLibre WMTS pattern; NASA GIBS imagery is background only, while trend values remain from GISTEMP. A live tile request returned HTTP 200.
- [x] Removed the M7 comparison control from the frontend before deployment; the comparison API route remains because section 12 lists it as an M5 endpoint.
- [x] Added plain-language p-value, confidence-interval, and significance explanations in English and French.
- [x] Added English/French explanation for a non-significant result; demo dialog cites NASA GISTEMP and the verified Arctic-amplification paper.
- [x] Deferred Hamed-Rao values from the MVP summary and main results; the advanced method remains documented and available in the API for the post-M8 interface.
- [ ] Verify that the wizard's questions and answers form the required guided detective path, and that both required demos have checked sourced context and actual result verdicts.
- [ ] Verify small-screen behavior and complete an actual browser walkthrough; these M6 acceptance checks remain outstanding.
- [x] Added frontend utility tests for rate/p-value formatting and fitted-line display. Direct npm dependencies are pinned; Node/npm versions are specified in `.nvmrc` and `package.json`.
- [x] `npm install` succeeded; direct dependencies are pinned and `web/package-lock.json` is available for reproducible installs.
- [x] `npm test` passes (4 frontend utility tests); `npm run build` passes type-checking and production bundling.
- [x] Local Vite and API are running. `GET /` and proxied `GET /api/variables` both returned HTTP 200.
- [ ] Manual mobile/browser review remains outstanding. Build reports a large JavaScript bundle (1.50 MB minified, 452 KB gzip); code splitting would improve first load.

## M8 preparation and required access

- [x] Added API and web Dockerfiles, Compose topology, Caddy HTTPS routing, persistent certificate storage, restart policies, and read-only processed-data mounts. `docker compose config` succeeds.
- [ ] `make deploy` currently starts Compose locally; it does not send the derived Zarr/tiles to a remote host as required by section 14.
- [ ] Deployment requires the server address, SSH user plus key path (or an agent configured with that key), a public domain pointed to the host, and confirmation that inbound 80/443 are open.
- [ ] Set `SITE_DOMAIN` in the server's ignored `.env` file. Deployed GISTEMP data do not require Earthdata credentials.

## M0 acceptance summary

- Setup and tests pass locally after pinning Python 3.11, pandas, and stable Zarr 2.18.7 (Zarr 3 caused an async open deadlock in this environment).
- Earthdata login criterion passed. `make setup && make test` passes locally; a minimal lint/test GitHub Actions workflow is configured.

## Audit result and next steps

- M0 and M1 have recorded evidence and their local acceptance checks pass.
- M2, M3, M4, M5, and M6 are partial; do not describe them as accepted until the unchecked requirements above pass.
- Milestone branches exist for M2, M4, M5, and M6; only the M0/M1 baseline is on `main`. Do not merge incomplete milestones.
- M8 has not started: the brief requires a public host, domain, deployment access, open ports 80/443, and an HTTPS end-to-end check. No alternative host has been selected.
- Keep GISTEMP as the only scientific dataset until the M8 MVP is deployed and working.
- Do not start or extend M7 before M8. The comparison and Rigorous result controls are not shown in the MVP frontend.
