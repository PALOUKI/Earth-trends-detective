# Project progress

Updated: 2026-11-02

## Current milestone: M1b — intégration multi-variable (données et API locales prêtes)

- [x] Read the full `AGENT_BRIEF.md`; section 1 bis governs scope and sequencing.
- [x] Confirmed the GISTEMP v4 download page and selected gridded NetCDF product are published by NASA GISS. The official compressed file URL is `https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz`.
- [x] Added pinned Python dependencies, `uv`, Make targets, CI, and secret-safe environment template.
- [x] `uv sync --all-groups` succeeds with Python 3.11; pytest and Ruff pass locally.
- [x] Earthdata environment login succeeded and a live CMR search request completed; CMR returned zero GISTEMP records, consistent with GISTEMP being served directly by NASA GISS and not cataloged here as a CMR granule product.
- [ ] Deployment server/domain credentials are not available; M8 deployment cannot be completed until an endpoint and deployment access are available.
- [x] Portée corrigée selon l'énoncé officiel : l'objectif livré couvre plusieurs variables NASA, pas GISTEMP seul.
- [x] Requête CMR réelle : MOD13C2 v061 trouvé et un granule mondial de janvier 2024 téléchargé (94 485 525 octets). Le fichier révèle NDVI/EVI mensuels à 0,05°, facteur d'échelle 1/10000 et variable de qualité pixel.
- [x] Dépendance HDF4 `pyhdf==0.11.6` ajoutée ; adaptateur MOD13C2 NDVI/EVI écrit pour masquer les pixels Fill et rangs qualité >1, agréger en grille 2° et produire Zarr.
- [x] Tests unitaires de conversion/masquage/agrégation MODIS : 2 passés.
- [x] CMR interrogé en direct : 319 granules mensuels de février 2000 à août 2026. Le téléchargeur reprend les transferts interrompus avec requêtes Range, vérifie la taille/HDF4 et ne promeut que les granules lisibles. 148 granules validés en local ; une fenêtre de 139 mois consécutifs (2000-02–2011-08) a été traitée.
- [x] Pipeline tendances/tuiles, extraction régionale, sérialisation API et sélecteur d'interface généralisés aux identifiants de variables. NDVI et EVI sont maintenant des analyses prêtes avec leurs séries, statistiques de tendance, COG et cartes XYZ calculés.
- [x] L'adaptateur exige au moins 120 mois consécutifs et l'analyse des indices MODIS enlève la climatologie mensuelle par cellule. Les tendances et cartes NDVI/EVI ont été générées sur la fenêtre complète disponible ; les fenêtres 2010-fin et 2015-fin sont exclues car elles n'ont pas 120 mois.
- [x] Après approbation Earthdata de NASA GESDISC DATA ARCHIVE, requêtes CMR authentifiées réussies pour MERRA-2, GLDAS, GPM, AIRS et OMI ; lectures Range HTTP 206 réelles de 4 Ko obtenues pour chaque lien de fichier.
- [x] Granules réels GPM, OMI et AIRS téléchargés. Métadonnées confirmées dans les fichiers : GPM `Grid/precipitation` en mm/hr, `TimeInterval=MONTH`, DOI 10.5067/GPM/IMERG/3B-MONTH/07 ; OMI `ColumnAmountNO2TropCloudScreened` en molec/cm2. Le champ AIRS `SurfAirTemp_A` et son unité K sont confirmés par l'échantillon et le guide NASA ; il reste à construire sa série multi-annuelle.
- [x] Téléchargé et contrôlé le jeu GPM complet retourné par CMR : 309 granules mensuels (2000-01–2025-09), dont 121 récupérés après reprise ; 309 fichiers HDF5 validés, série sur grille 2° produite, tendances et cartes XYZ `full`, `2010-fin`, `2015-fin` générées. L'API signale GPM `analysis_ready`.
- [x] Adaptateurs GPM mensuel et OMI quotidien-vers-mensuel ajoutés avec tests de grille, Fill, unités et dates ; l'agrégation OMI est préparée pour une série 2005–2014. Les téléchargements historiques et produits d'analyse OMI restent à exécuter.
- [x] Approbation Earthdata vérifiée par téléchargement : le champ MERRA-2 `EVAP` (kg m-2 s-1) et le champ GLDAS `SoilMoi0_10cm_inst` (kg m-2) ont été lus dans de vrais fichiers NASA. Les téléchargements de 120 mois 2000–2009 sont en cours avec contrôle de chaque NetCDF avant inclusion.
- [x] OMI 2005–2014 : 3 646 granules `.he5` vérifiés, série mensuelle 120 mois, tendance globale et tuiles XYZ générées ; son statut API est `analysis_ready`.
- [x] Tests d'adaptateurs MERRA-2/GLDAS : lecture de vrais noms de champs configurés, unité, masquage des Fill, grille cible et conservation des mois manquants couverts par tests synthétiques.
- [x] AIRS3STM v7 : 120/120 granules mensuels validés pour 2002-09–2012-08 ; Zarr, tendance et tuiles générés, statut API `analysis_ready`.
- [x] MERRA-2 EVAP et GLDAS Noah soil moisture : 120/120 mois chacun pour 2000-01–2009-12 ; séries Zarr, tendances et tuiles générées. Le granule MERRA-2 2001-09 initialement tronqué a été repris par HTTPS authentifié puis validé ; les deux statuts API sont `analysis_ready`.
- [x] `/api/variables` inclut désormais la métadonnée `windows` configurée pour MERRA-2, GLDAS, AIRS et OMI ; le contrat FastAPI ne rejette plus les nouveaux produits prêts. Tests API vérifient la cohérence entre catalogue et liste analysable.
- [x] Parcours API régional exécuté sur les huit variables `analysis_ready` dans l'emprise Amazon : les huit réponses sont HTTP 200 avec séries et statistiques.
- [x] Vérification locale complète après intégration : 46 tests Python et 6 tests frontend passent ; `npm run build` passe. L'interface répertorie huit produits analysables via `/api/variables`.
- [x] `make test` ne peut pas démarrer dans ce bac à sable car uv écrit dans un cache utilisateur en lecture seule ; avant le nouveau test de reprise OMI, `.venv/bin/pytest -q` passait (43 tests) ; les tests OMI ciblés (4), les tests API ciblés (3), Ruff et `git diff --check` passent.
- [x] Téléchargeur OMI remplacé par des requêtes authentifiées avec timeout de connexion/lecture, reprise des fragments validés par `Content-Range` et validation HDF-EOS après réception ; test de reprise ajouté.
- [x] Le message du parcours qualité de l'air indique clairement que les données NASA OMI et les cartes ne sont pas encore prêtes. Correction du parcours Vue : une suggestion indisponible ne change plus la variable sélectionnée et le message n'est plus effacé par le watcher.
- [x] `make test` passe avec les nouveaux tests GPM/OMI (39 tests au total) ; Ruff passe sur les modules d'ingestion et les fichiers API/pipeline modifiés.

## Decisions and blockers

- Les huit variables listées au catalogue sont analysables localement ; les fenêtres courtes MERRA-2, GLDAS, AIRS et OMI proposent uniquement `full`, conformément à leur période réellement acquise.
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
- [x] Implemented per-pixel OLS slope/95% CI/t-test, Sen slope/95% CI, classic Mann-Kendall, Hamed-Rao, and FDR with Numba `@njit(parallel=True)`, `xarray.apply_ufunc`, and Dask. FDR uses Hamed-Rao p-values.
- [x] Added equivalence tests against SciPy and pyMannKendall over 1,000 seeded pixels, including tied and missing-value cases; added no-trend false-positive simulation for MK and Hamed-Rao.
- [x] Added `--annual` monthly-vs-annual sign/significance concordance outputs, full trend-statistic Zarr schema, and a multiband EPSG:4326 COG writer with named bands.
- [ ] Full-grid benchmark: 16,200 cells × 1,761 months ran in 161.42 seconds on this 4-core container, above the brief's <120 second target. M2 remains partial pending optimization or a documented resource-qualified target.

## M3 — scientific validation (partial)

- [x] Compared 561 monthly global series (1980-01–2026-09) to the NASA GISS published global CSV: bias 0.00267 K, RMSE 0.05006 K, maximum absolute difference 0.18366 K.
- [x] Grid weighted and published global linear slopes agree to 0.0000008 K/year (0.0210564 vs 0.0210556 K/year).
- [x] Regional grid results show 0.06926 K/year for 70–90°N and 0.03408 K/year for 30–60°N, matching the published qualitative Arctic amplification pattern (England et al., 2021; DOI 10.1029/2021GL094086).
- [x] Reproducible code and the expected/obtained summary are in `notebooks/01_validation_gistemp.ipynb`; NASA source and access date are in `docs/DATA_SOURCES.md`.
- [ ] Live [Giovanni no-script catalog](https://giovanni.gsfc.nasa.gov/giovanni/daac-bin/noscript.cgi) checked on 2026-11-01; an exact `GISTEMP` search returned no result. Since section 2 requires one GISTEMP variable until deployment, no different dataset was substituted. Giovanni validation is blocked by the absence of the selected product and M3 is not accepted.

## M4 — map products and visual encoding (XYZ generation implemented; depends on incomplete M2 map statistics)

- [x] Generated full OLS, Sen, classic Mann-Kendall, Hamed-Rao, and Hamed-Rao/BH significance grids for `full`, `2010-fin`, and `2015-fin` from the actual GISTEMP Zarr.
- [x] `make trends` writes the complete metric set to Zarr and a 12-band EPSG:4326 COG. `make trends TRENDS_FLAGS=--annual` additionally writes annual slope/p/significance and monthly-vs-annual concordance fields.
- [x] Replaced the earlier single-image overlay (which did not meet the brief) with pinned `rio-tiler==9.4.9` raster XYZ tiles for the slope and nonsignificance stipple layers, zooms 0–5.
- [x] Tile files are laid out under `data/tiles/<id>/<window>/<layer>/{z}/{x}/{y}.png`; `/api/trend` returns tile URL templates, and Caddy serves tiles with long cache headers.
- [x] Palette is diverging and centered on zero, with symmetric clipping at the 98th percentile of absolute slopes; layer metadata includes K/year, bounds, scale, and interpretation.
- [x] Tests verify XYZ paths, palette metadata, zoom bounds, and tile serving. Full XYZ layers were generated for all three windows from the current OLS/FDR data.
- [x] Rebuilt all XYZ windows from full M2 outputs. The color layer is OLS slope, and the stipple layer reflects Hamed-Rao p-values after Benjamini-Hochberg FDR.

## M5 — API (partial)

- [x] FastAPI routes are implemented for health, variables, suggestions, regions, regional analysis, point analysis, comparisons, trend metadata, and XYZ tiles.
- [x] Added `GET /api/export`: regional monthly series as CSV, precomputed map layers as PNG, and generated multiband GeoTIFFs.
- [x] Added Pydantic response models for variables, analyses, comparisons, and map metadata.
- [x] Added Pydantic response models to the region and point endpoints.
- [ ] Broader contract checks against every field and behavior required by section 12 remain; M5 is not accepted yet.
- [x] Added on-demand Pettitt statistics (candidate date, analytic p-value, statistic, verdict) to point/region API responses; tests verify the rank statistic, analytic formula, and mapping to the original date. The frontend marker remains post-deployment M7.
- [x] `/api/suggest` now returns a matching predefined region ID alongside a variable suggestion; unsupported themes remain explicitly unavailable until data exist.
- [x] `/api/trend` includes map-wide valid/significant/non-significant cell counts when its processed Zarr is present.
- [x] Deterministic summaries are provided in English and French; OpenAPI docs are available at `/docs`.
- [x] Async HTTP contract tests cover the catalog, health, map layers, regional analysis, and clicked point response.
- [x] L'API expose un catalogue vérifié avec états `analysis_ready`, `sample_downloaded`, `acquiring`, `series_processed` et `blocked_eula` ; les routes de série, point, tendance, tuiles et export sélectionnent leur stockage via l'identifiant variable. Les résumés et unités dépendent de la variable et citent son DOI dans l'interface.
- [x] Tests use `httpx` ASGI calls and synthetic fixture datasets; all API endpoint tests pass.
- [x] Warm GISTEMP point endpoint measured at 206–223 ms locally after an initial 575 ms cold call; the brief's <300 ms target is met after data/cache warm-up.
- [x] CORS defaults to the local frontend origin and is configurable by `ALLOWED_ORIGINS` for deployment.

## M6 — frontend MVP (partial; manual and acceptance review outstanding)

- [x] Reviewed the supplied Stitch design system and explorer, wizard, and demo screens. Applied the NASA-blue palette, Inter typography, 8px spacing rhythm, analytical side panel, map workspace, and three-step investigation wizard.
- [x] Implemented Vue 3 + Vite + TypeScript UI with MapLibre, ECharts, English default/French switch, region controls, rectangle drawing, period presets, point clicks, bilingual summaries, methods, and two GISTEMP guided examples as required for M6.
- [x] Ajout d'un sélecteur issu du catalogue vérifié ; les variables ont un état explicite et restent non sélectionnables tant que leurs traitements et cartes ne sont pas disponibles. Les appels région/point/carte transmettent maintenant l'identifiant de variable.
- [x] Replaced the dated MODIS true-color base image with GIBS `BlueMarble_NextGeneration`, verified in the live WMTS capabilities and by a real HTTP 200 tile request; GIBS remains geographic background imagery only.
- [x] Trend tiles preserve the native GISTEMP grid with nearest-neighbor display resampling, reduced overlay opacity, and transparent missing cells; stipple marks remain crisp. These are display choices only; statistical source values are unchanged.
- [x] Regional comparison is now exposed in the frontend because comparing opposite regional trends is part of the official challenge scope (section 1 bis).
- [x] Fixed the comparison variable selector: `/api/variables` already returns only analysis-ready products, while its response schema omits catalog `status`; the frontend no longer filters that response by the omitted field. Inventory requests now settle independently so a failed catalogue or region request does not discard ready variables.
- [x] Comparison validation and API error messages render above the region selectors, next to the comparison controls.
- [x] Integrated the supplied Stitch landing, variable catalogue, regional comparison, methods, about/credits, and export screens as application views. All dataset names, statuses, periods, sources, and DOI links are populated from the live API catalogue; comparison results and exports use the existing analysis endpoints.
- [x] Added responsive navigation and single-column layouts for the new catalog, comparison, and landing screens on narrow viewports.
- [x] Added plain-language p-value, confidence-interval, and significance explanations in English and French.
- [x] Added English/French explanation for a non-significant result; demo dialog cites NASA GISTEMP and the verified Arctic-amplification paper.
- [x] Deferred Hamed-Rao values from the MVP summary and main results; the advanced method remains documented and available in the API for the post-M8 interface.
- [ ] Verify that the wizard's questions and answers form the required guided detective path, and that both required demos have checked sourced context and actual result verdicts.
- [ ] Verify small-screen behavior and complete an actual browser walkthrough; these M6 acceptance checks remain outstanding.
- [ ] M6 reste partiel jusqu'à ce que le premier produit en plus de GISTEMP soit analysable dans l'interface et que le parcours multi-variable soit vérifié dans un navigateur.
- [x] Added frontend utility tests for rate/p-value formatting and fitted-line display. Direct npm dependencies are pinned; Node/npm versions are specified in `.nvmrc` and `package.json`.
- [x] `npm install` succeeded; direct dependencies are pinned and `web/package-lock.json` is available for reproducible installs.
- [x] `npm test` passes (6 frontend tests); `npm run build` passes type-checking and production bundling.
- [x] Local Vite and API are running. `GET /` and proxied `GET /api/variables` both returned HTTP 200.
- [ ] Manual mobile/browser review remains outstanding. The local API health and catalog endpoints responded, but this session could not confirm the Vite listener from a separate shell; browser acceptance remains pending. Build reports a large JavaScript bundle (1.52 MB minified, 457 KB gzip); code splitting would improve first load.

## M8 preparation and required access

- [x] Added API and web Dockerfiles, Compose topology, Caddy HTTPS routing, persistent certificate storage, restart policies, and read-only processed-data mounts. `docker compose config` succeeds.
- [x] `make deploy` invokes `deploy/deploy.sh`, which sends only processed Zarr/COG/XYZ products for all selected variables over SSH/rsync, builds Compose remotely, and checks the HTTPS health endpoint.
- [ ] Remote execution remains blocked until the host, SSH user/key access, public DNS domain, and inbound 80/443 status are supplied. Deployed GISTEMP data do not require Earthdata credentials.

## M0 acceptance summary

- Setup and tests pass locally after pinning Python 3.11, pandas, and stable Zarr 2.18.7 (Zarr 3 caused an async open deadlock in this environment).
- Earthdata login criterion passed. `make setup && make test` passes locally; a minimal lint/test GitHub Actions workflow is configured.

## Audit result and next steps

- M0 and M1 have recorded evidence and their local acceptance checks pass.
- M2, M3, M4, M5, and M6 are partial; do not describe them as accepted until the unchecked requirements above pass.
- Milestone branches exist for M2, M4, M5, and M6; only the M0/M1 baseline is on `main`. Do not merge incomplete milestones.
- M8 has not started: the brief requires a public host, domain, deployment access, open ports 80/443, and an HTTPS end-to-end check. No alternative host has been selected.
- GISTEMP, MODIS NDVI/EVI, GPM precipitation, MERRA-2 EVAP, GLDAS soil moisture, AIRS temperature, and OMI NO₂ all have local processed series, trend products, map tiles, and regional API responses. Manual frontend/browser acceptance and remote M8 deployment remain outstanding.
- Do not start unrelated M7 extensions before M8. Regional comparison is included as a core challenge workflow; the advanced Rigorous result controls remain deferred.
