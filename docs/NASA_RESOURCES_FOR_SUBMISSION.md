# NASA resources used by Earth Trend Detective

Audit date: 2026-11-15. This document is the project-specific source list for the NASA Space Apps Challenge submission form fields **Link Text** and **Link URL**. The URLs below are full URLs. Product versions, CMR collection names, data fields, and local analysis coverage were checked against the project catalog/files; CMR collection searches for the six Earthdata products returned one matching collection for each requested short name and version on the audit date.

## Entries to paste into the NASA submission form

These are resources that provide data or imagery actually used by the application, plus the GISTEMP reference series used for validation. The seven analytical products provide eight selectable analysis variables because MOD13C2 provides both NDVI and EVI.

| Link Text | Link URL | Exact use in this project |
| --- | --- | --- |
| NASA GISS GISTEMP v4 — Land-Ocean Temperature Index gridded monthly anomalies | https://data.giss.nasa.gov/gistemp/data_v4.html | Main temperature-analysis input. The application downloads the official compressed 2° × 2° monthly NetCDF [direct file](https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz); local processed record is 1880-01–2026-09. This is a blended land-surface-air and sea-surface temperature anomaly product, not absolute temperature. No CMR short name is used. |
| NASA Terra MODIS MOD13C2 v061 — monthly NDVI and EVI | https://doi.org/10.5067/MODIS/MOD13C2.061 | One monthly vegetation-index dataset used for two selectable variables, NDVI and EVI. CMR short name/version: `MOD13C2` / `061`; collection concept ID returned by the audit query: `C2565788914-LPCLOUD`. Local processed coverage: 2000-02–2011-08. |
| NASA MERRA-2 M2TMNXFLX v5.12.4 — monthly surface flux diagnostics | https://doi.org/10.5067/0JRLVL8YV2Y4 | Model-derived evaporation flux, field `EVAP`, unit `kg m-2 s-1`. CMR short name/version: `M2TMNXFLX` / `5.12.4`; concept ID: `C1276812868-GES_DISC`. Local processed coverage: 2000-01–2009-12. |
| NASA GLDAS Noah v2.1 — monthly 0.25° land-surface fields | https://doi.org/10.5067/SXAVCZFAQLNO | Model-derived topsoil moisture, field `SoilMoi0_10cm_inst`, unit `kg m-2` (0–10 cm layer). CMR short name/version: `GLDAS_NOAH025_M` / `2.1`; concept ID: `C1342986036-GES_DISC`. Local processed coverage: 2000-01–2009-12. |
| NASA GPM IMERG Final v07 — monthly precipitation | https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 | Monthly precipitation rate, field `Grid/precipitation`, unit `mm/hr`. CMR short name/version: `GPM_3IMERGM` / `07`; concept ID: `C2723754851-GES_DISC`. The application contains 309 monthly granules, 2000-01–2025-09. |
| NASA AIRS/Aqua L3 v7.0 — monthly standard physical retrieval, AIRS-only | https://doi.org/10.5067/UBENJB9D3T2H | Surface atmospheric temperature, field `SurfAirTemp_A` (ascending), unit K. CMR short name/version: `AIRS3STM` / `7.0`; concept ID: `C1701805662-GES_DISC`. Local processed coverage: 2002-09–2012-08. This is an atmospheric temperature variable, not an air-pollution measure. |
| NASA Aura OMI OMNO2d v004 — daily gridded tropospheric nitrogen dioxide | https://doi.org/10.5067/AURA/OMI/DATA3407 | Cloud-screened tropospheric NO₂ column, field `ColumnAmountNO2TropCloudScreened`, unit molecules/cm²; daily observations are aggregated to monthly values by the project pipeline. CMR short name/version: `OMNO2d` / `004`; concept ID: `C3333493715-GES_DISC`. Local processed coverage: 2005-01–2014-12. It is a satellite column measurement and not a ground-level monitor. |
| NASA GIBS Blue Marble: Next Generation — map basemap | https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/ | NASA imagery used only for geographic context in the Explorer and comparison maps and as the base globe texture on the landing page. The app's live map requests the GIBS layer `BlueMarble_NextGeneration`; the exact tile template and a verified WMS request are recorded below. It is not used in statistical calculations. |
| NASA Terra MODIS MOD11A1 v061 — daily daytime land-surface temperature (globe visual only) | https://doi.org/10.5067/MODIS/MOD11A1.061 | Used only through the NASA GIBS visualization layer `MODIS_Terra_L3_Land_Surface_Temp_Daily_Day`, snapshot date `2025-07-01`, on the landing-page globe. No MOD11A1 scientific values enter the Explorer trend analysis. The matching [NASA Worldview layer](https://worldview.earthdata.nasa.gov/?l=Coastlines_15m,MODIS_Terra_L3_Land_Surface_Temp_Daily_Day) is also linked. |
| NASA GISS GISTEMP v4 — published global monthly series (validation reference) | https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts%2BdSST.csv | Independent published global monthly series compared with the area-weighted mean of the processed gridded GISTEMP file in `notebooks/01_validation_gistemp.ipynb`. It is a validation reference, not an application analysis input. The official [GISTEMP downloads page](https://data.giss.nasa.gov/gistemp/data_v4.html) links this CSV. |

## Additional NASA access and documentation resources used

These resources support dataset discovery, acquisition, product interpretation, or map rendering. They do not represent additional independent data variables.

| Resource name | Full URL | Role |
| --- | --- | --- |
| NASA Earthdata Search | https://search.earthdata.nasa.gov/ | NASA collection/granule discovery entry point. |
| NASA Common Metadata Repository (CMR) Search API documentation | https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html | API documentation for the real CMR searches used to verify product short names and versions. |
| NASA GIBS Access Basics | https://nasa-gibs.github.io/gibs-api-docs/access-basics/ | Documentation for NASA imagery tile services used by the maps and the landing-page globe. |
| NASA GES DISC IMERG Final Run data page | https://gpm.nasa.gov/node/3328 | NASA GPM page linking to the monthly GPM_3IMERGM v07 GES DISC collection used here. |
| NASA AIRS V7 L3 Product User Guide | https://docserver.gesdisc.eosdis.nasa.gov/public/project/AIRS/V7_L3_User_Guide.pdf | Checked to identify `SurfAirTemp_A` as surface atmospheric temperature and verify its unit is kelvin. |
| NASA MODIS Vegetation Indices V6.1 User Guide | https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf | Product documentation for the MOD13C2 NDVI/EVI source. |
| NASA OMI OMNO2 README | https://ozoneaq.gsfc.nasa.gov/content/public/OMI/READMEs/README.OMNO2.pdf | Product and field documentation for OMI tropospheric NO₂. |
| NASA GISTEMP associated publication — Lenssen et al. (2024) | https://doi.org/10.1029/2023JD040179 | Scholarly publication cited with the GISTEMP product in project data credits; it is a publication, not an additional data input. |
| NASA Earthdata `earthaccess` search/access client documentation | https://earthaccess.readthedocs.io/en/latest/ | Python client used by the ingestion code to search NASA Earthdata/CMR and retrieve granules. This is access software, not an additional data product. |

### Exact NASA GIBS service requests used/verified

The two WMS requests below were sent to the live NASA GIBS service on 2026-11-15 and returned HTTP 200. The static globe textures in `web/public/images/` match the corresponding world imagery and, for the LST overlay, the stated layer/date; these are visualization assets only. The runtime tile template is the URL configured in the app and was previously verified with a real tile request, as recorded in `DATA_SOURCES.md`.

- **Blue Marble equirectangular WMS request:** `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=BlueMarble_NextGeneration&STYLES=&FORMAT=image%2Fjpeg&TRANSPARENT=false&HEIGHT=512&WIDTH=1024&CRS=EPSG%3A4326&BBOX=-90%2C-180%2C90%2C180`
- **MODIS Terra LST dated WMS request:** `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=MODIS_Terra_L3_Land_Surface_Temp_Daily_Day&STYLES=&FORMAT=image%2Fpng&TRANSPARENT=true&HEIGHT=1024&WIDTH=2048&CRS=EPSG%3A4326&BBOX=-90%2C-180%2C90%2C180&TIME=2025-07-01`
- **Live map tile template in the app:** `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`. `{z}`, `{y}`, and `{x}` are tile-coordinate placeholders expanded by MapLibre; this is a template, not a single tile URL.

## NASA tools surfaced to users, with an important limitation

The Resources screen links these NASA tools, and the app supports importing a compatible user-downloaded CSV into its generic monthly analysis route. The app does **not** automate downloads from these portals or claim that its eight preprocessed datasets came from them. List them on the submission form only if the question includes resources offered to users; do not describe them as sources of the current built-in analysis records.

| Link Text | Link URL | Actual integration |
| --- | --- | --- |
| NASA GES DISC Giovanni | https://giovanni.gsfc.nasa.gov/giovanni/ | External portal link; user can import a compatible manually exported CSV. No Giovanni validation result is claimed. |
| NASA GES DISC Hydrology Time Series | https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series | External portal link; user can import a compatible manually exported CSV. No built-in automated download or completed sample analysis is claimed. |
| NASA AppEEARS | https://appeears.earthdatacloud.nasa.gov/ | External portal link; user can import a compatible manually exported CSV. No built-in automated download or completed sample analysis is claimed. |

## Deliberate exclusions and wording guardrails

- Do not list NOAA Climate Data Online or CUAHSI as NASA resources. They are non-NASA optional sources also surfaced by the application.
- Do not say NASA GIBS tiles supply the scientific trend values: GIBS is imagery for visual context; the analysis overlays come from the project's processed data products.
- Do not claim that NASA Hydrology Time Series, Giovanni, or AppEEARS generated the project's built-in time series. They are manual external workflows only.
- Do not claim the NASA-hosted SeaWiFS paper in the challenge Resources tab is an integrated dataset or a completed validation source. It is not used by the current analysis workflow.
- GISTEMP has no CMR short name in this project: the live CMR search for `GISTEMP` found no collection, and the data are downloaded from the NASA GISS page. Do not invent one.
- The current local periods are shorter than the full source-record availability for some products. Use the coverage stated above, not the entire collection's advertised range, when describing what this running project can analyze.

## Verification record

- NASA GISS's downloads page and the selected gridded NetCDF link were checked; the official page describes monthly anomaly grids on a 2° × 2° grid.
- CMR was queried live by `short_name` and `version` on 2026-11-15. The six exact product/version queries each returned one collection: MOD13C2/061, M2TMNXFLX/5.12.4, GLDAS_NOAH025_M/2.1, GPM_3IMERGM/07, AIRS3STM/7.0, and OMNO2d/004. Their returned concept IDs are included above.
- The live API catalog returned all eight analysis variables with `analysis_ready` status; corresponding processed Zarr stores and trend stores are present locally. The periods recorded above are the actual local periods, not claims about the full source archive.
- NASA GIBS requests for Blue Marble and the dated MODIS LST layer returned HTTP 200. The files and frontend code use these only as display imagery.
- GISTEMP's published global CSV is loaded by the validation notebook. The notebook explicitly says that a Giovanni cross-check has not been completed.

## Space Agency Partner & Other Data

Audit date: 2026-11-15. This section is for the second submission-form field. It separates sources that supply content used by the project from user-facing links and software used to build/run it. Every listed URL was checked with a live HTTP request on the audit date, except where an individual service is explicitly described as a URL template. The project repository and its two local image assets are public at the checked `develop` branch URL.

### Copy-ready data, map, and design resources

| Link Text | Link URL | Exact use and source notes |
| --- | --- | --- |
| Natural Earth — Admin 0 countries GeoJSON (110m) | https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson | Used in the country picker for country names/reference coordinates and on maps for country borders and labels. Natural Earth states its map data are public domain: https://www.naturalearthdata.com/about/terms-of-use/. Attribution is not required by its terms; the project still credits it in the app. |
| Natural Earth — ocean polygons GeoJSON (110m) | https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_ocean.geojson | Used as a geographic ocean fill beneath the map overlays. Same Natural Earth public-domain terms as above. |
| Natural Earth — terms of use | https://www.naturalearthdata.com/about/terms-of-use/ | License/attribution terms for the two Natural Earth map datasets used above. |
| RESOLVE 2017 terrestrial ecoregions — ArcGIS FeatureServer layer 0 | https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0 | This is the ecological-region layer used when a user searches for a country. The app takes the country's Natural Earth reference point, queries which RESOLVE ecoregion contains it, then draws that ecoregion and uses its polygon as the analysis mask. It is not a country-boundary layer and does not choose a random neighboring region. The service metadata calls it the RESOLVE Ecoregions dataset (updated 2017), but leaves `copyrightText` blank and does not state a license; public access alone does not establish reuse permission. Dataset background: https://ecoregions2017.appspot.com/. |
| CUAHSI HIS Central — time-series catalog web service | https://hiscentral.cuahsi.org/webservices/hiscentral.asmx | Integrated in the Sources view: the app sends a live spatial/date/variable query to `GetSeriesCatalogForBox3` and displays the returned station metadata. The service documents this method as returning metadata matching the query: https://hiscentral.cuahsi.org/webservices/hiscentral.asmx. |
| CUAHSI WaterOneFlow — service documentation | https://his.cuahsi.org/wofws.html | Integrated retrieval protocol. For a chosen catalog result, the app calls the provider's registered `GetValues` operation and analyzes the returned station observations. Provider service URLs are returned dynamically by HIS Central; there is not one fixed provider URL for all stations. These are station observations, not NASA data or gridded regional averages. |
| NOAA Climate Data Online (CDO) | https://www.ncei.noaa.gov/cdo-web/ | A link shown in the Sources view for users to visit/download station data. The app does not call NOAA CDO or use NOAA observations in its built-in analysis. |
| MapLibre demo glyph service — Open Sans / Arial Unicode MS | https://demotiles.maplibre.org/font/Open%20Sans%20Regular,Arial%20Unicode%20MS%20Regular/0-255.pbf | Public glyph resource used by the MapLibre style to render country-label text. This concrete URL returned HTTP 200; the style uses a glyph URL template with font/range placeholders. It supplies fonts only, not map data. |
| Google Fonts — Poppins | https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap | Web font requested by `web/index.html` and used by the interface. |
| Google Stitch | https://stitch.withgoogle.com/ | The owner-provided Stitch screens were used as visual design references. The running Vue interface was implemented in the project; Stitch is not a runtime dependency and its generated mockup assets are not embedded as page screenshots. |
| Earth Trend Detective — public source repository | https://github.com/PALOUKI/Earth-trends-detective | Project source code, including the data/API/frontend implementation and package manifests. Repository page returned HTTP 200 during this audit. |
| Earth Trend Detective — application logo (AI-generated with Google Gemini) |  | Used in the header and footer; the interface marks it “SI-generated.” The owner confirmed Google Gemini as the generator. Original-source link intentionally left blank for the owner to fill. The public project copy is at https://raw.githubusercontent.com/PALOUKI/Earth-trends-detective/develop/web/public/images/app-logo.png. |
| Upward arrow image from Google search |  | Used decoratively on the landing hero. The owner found it through Google search; that is not the original source URL. Original-source link intentionally left blank for the owner to fill. The public project copy is at https://raw.githubusercontent.com/PALOUKI/Earth-trends-detective/develop/web/public/images/hero-up-arrow.png. Confirm the original creator's reuse terms before submission. |

### Statistical methods and implementation references

These are references exposed in the Methods view or used directly by the statistical implementation/tests. Method citations are not data sources.

| Link Text | Link URL | Use |
| --- | --- | --- |
| SciPy — `linregress` | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html | Linear regression slope and t-test used in the base trend results. |
| SciPy — `theilslopes` | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html | Sen/Theil slope and confidence interval used in the base results. |
| pyMannKendall | https://github.com/mmhs013/pyMannKendall | Runtime reference implementation used for Mann–Kendall tests, including the advanced Hamed–Rao result. |
| Hamed & Rao (1998) — modified Mann–Kendall test | https://doi.org/10.1016/S0022-1694(97)00125-X | Primary method reference for the autocorrelation-adjusted Mann–Kendall procedure described in Methods. |
| Statsmodels — multiple-testing correction | https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html | Runtime Benjamini–Hochberg false-discovery-rate correction for the grid analysis. |
| Statsmodels — STL decomposition | https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html | Method/API reference for seasonal decomposition in the time-series display. |
| Wilks (2016) — The Stippling Shows Statistically Significant Grid Points | https://read.nxtbook.com/ametsoc/bams/december2016/essay_thestipplingshows.html | Public American Meteorological Society reading page for the article cited as rationale for multiple-testing/FDR treatment of gridded results. DOI: https://doi.org/10.1175/BAMS-D-15-00267.1. |
| pyHomogeneity — Pettitt test reference implementation | https://github.com/mmhs013/pyHomogeneity | The project implements the Pettitt statistic itself; a test compares its statistic and analytic p-value to this reference. pyHomogeneity is not imported as a runtime dependency. |

### Direct software dependencies

These package versions come from the checked-in `pyproject.toml` and `web/package.json`. They are software, not scientific datasets. NASA's `earthaccess` is already listed in the NASA section; all other direct dependencies are recorded here so the non-NASA code/tools inventory is reproducible. Package documentation/home pages below are public.

| Link Text | Link URL | Role in this project |
| --- | --- | --- |
| Python 3.11+ | https://www.python.org/ | Backend and processing language. |
| uv | https://docs.astral.sh/uv/ | Python environment and dependency management. |
| FastAPI 0.115.12 | https://fastapi.tiangolo.com/ | JSON API framework. |
| Uvicorn 0.34.2 | https://pypi.org/project/uvicorn/ | ASGI application server. |
| Pydantic 2.11.4 | https://docs.pydantic.dev/ | API request/response validation. |
| NumPy 2.2.5 | https://numpy.org/doc/ | Numerical arrays and statistical calculations. |
| Numba 0.68.0 | https://numba.readthedocs.io/ | Compilation/acceleration of grid calculations. |
| pandas 2.2.3 | https://pandas.pydata.org/docs/ | Time-indexed series handling. |
| SciPy 1.15.3 | https://docs.scipy.org/doc/scipy/ | Statistical tests, regression, and confidence intervals. |
| xarray 2025.4.0 | https://docs.xarray.dev/ | Labeled multidimensional scientific arrays. |
| Dask array 2025.4.1 | https://docs.dask.org/en/stable/array.html | Chunked/lazy array processing. |
| Zarr 2.18.7 | https://zarr.readthedocs.io/en/support-v2/ | Chunked processed data stores; this documentation branch covers the Zarr 2 series pinned by the project. |
| netCDF4 1.7.2 | https://unidata.github.io/netcdf4-python/ | NetCDF input/output. |
| h5netcdf 1.6.1 | https://github.com/h5netcdf/h5netcdf | HDF5-backed NetCDF access. |
| h5py 3.16.0 | https://docs.h5py.org/ | HDF5 file access. |
| Pydap 3.5.9 | https://github.com/pydap/pydap | OPeNDAP data access support. |
| pyhdf 0.11.6 | https://github.com/fhs/pyhdf | HDF4 data access support. |
| pyMannKendall 1.4.3 | https://github.com/mmhs013/pyMannKendall | Mann–Kendall statistical methods. |
| rio-tiler 9.4.9 | https://github.com/cogeotiff/rio-tiler | Raster tile generation/reading for map layers. |
| Statsmodels 0.14.4 | https://www.statsmodels.org/ | Multiple-testing correction and time-series methods. |
| python-dotenv 1.1.0 | https://github.com/theskumar/python-dotenv | Local environment configuration. |
| HTTPX 0.28.1 | https://www.python-httpx.org/ | HTTP clients for source/service requests and API tests. |
| pytest 8.3.5 | https://docs.pytest.org/ | Backend and pipeline tests. |
| Ruff 0.11.8 | https://docs.astral.sh/ruff/ | Python linting and formatting. |
| Vue 3.5.13 | https://vuejs.org/ | Frontend framework. |
| Vite 6.1.0 | https://vite.dev/ | Frontend dev server and bundler. |
| TypeScript 5.7.3 | https://www.typescriptlang.org/docs/ | Frontend language/type checking. |
| MapLibre GL JS 5.3.0 | https://maplibre.org/maplibre-gl-js/docs/ | Interactive maps and map overlays. |
| Apache ECharts 5.6.0 | https://echarts.apache.org/ | Time-series charts. |
| vue-echarts 7.0.3 | https://github.com/ecomfe/vue-echarts | Vue integration for Apache ECharts. |
| Three.js 0.187.0 | https://threejs.org/docs/ | Landing-page rotating globe visualization. |
| @types/three 0.187.0 | https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/three | TypeScript definitions for Three.js. |
| @vitejs/plugin-vue 5.2.1 | https://github.com/vitejs/vite-plugin-vue | Vue compiler integration for Vite. |
| jsdom 26.0.0 | https://github.com/jsdom/jsdom | Browser DOM environment for frontend tests. |
| Vitest 3.0.8 | https://vitest.dev/ | Frontend unit tests. |
| vue-tsc 2.2.0 | https://github.com/vuejs/language-tools | Vue/TypeScript type checking. |

### Items intentionally not represented as used data/resources

- KNMI Climate Explorer, GEO.ca, RADARSAT, SWOT, the CSA ecosystem article, the CSA SAR tutorial, and the two general statistics articles are recorded in `CHALLENGE_RESOURCES.md` as challenge-provided/potential references. The app does not currently use their data, software, or content in its analysis or interface, so this document does not claim they were used.
- The NASA Giovanni, NASA Hydrology Time Series, and AppEEARS portals are listed only in the NASA section above. NOAA CDO is the only non-NASA portal from that set linked in the current Sources view, and it remains a user-facing link rather than an integrated data source.
- NASA Blue Marble and MODIS imagery are listed in the NASA section; do not duplicate them as non-NASA material.
- ArcGIS service metadata does not state a license. The owner identified Gemini as the logo generator and Google search as how the arrow was found; the original image links are deliberately blank in the copy-ready rows for the owner to complete. Do not imply that public access or Google search results grant reuse permission.

### Live URL verification record

On 2026-11-15, the 58 unique URLs in this section were checked with live HTTP GETs. 57 returned 200. The DOI target for Wilks returned 403 to this automated client; an AMS-hosted public reading page for the same article returned 200 and is the copy-ready link. The single-font MapLibre glyph probes returned 404; the combined font stack used for the concrete verification returned 200. Dynamic WaterOneFlow provider URLs are returned by HIS Central at runtime and must be checked for the specific selected station. A successful HTTP response confirms public reachability, not a license grant or scientific suitability.
