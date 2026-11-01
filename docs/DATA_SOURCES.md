# Data sources

## NASA GISS GISTEMP v4

- **Product:** Land-Ocean Temperature Index, ERSSTv5, 1200 km smoothing; monthly temperature anomalies on a regular 2°×2° grid.
- **Publisher:** NASA Goddard Institute for Space Studies.
- **Version:** GISTEMP v4. The downloaded NetCDF history reports creation on 2026-10-08; the source is updated monthly.
- **Data URL:** [Compressed NetCDF](https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz)
- **Product page:** [GISTEMP v4 Data Downloads](https://data.giss.nasa.gov/gistemp/data_v4.html)
- **Accessed:** 2026-11-01.
- **Variable:** `tempanomaly`, unit K, 1761 monthly records from 1880-01 through 2026-09 in the downloaded file.
- **DOI / associated publication:** 10.1029/2023JD040179, Lenssen et al. (2024), *A GISTEMPv4 observational uncertainty ensemble*, cited by the NASA GISTEMP page. NASA asks users to cite the dataset page and the most recent scholarly publication.
- **Processing:** Converted source time coordinates to month starts; normalized longitude to [-180, 180]; retained native 2° grid; masked cells below 70% valid months or 120 valid months; wrote chunked Zarr v2. Values are already monthly anomalies and were not deseasonalized a second time.
- **CMR short name:** None used. A live authenticated `earthaccess` CMR search for `GISTEMP` returned zero records; this data source is obtained from the NASA GISS public download page.
- **Limitations:** This is a blended land-surface air and sea-surface temperature analysis, not absolute temperature. Coverage varies in space and time; the current endpoint can update historical values.

## NASA Terra MODIS MOD13C2 v061 vegetation indices

- **Product:** Vegetation Indices Monthly L3 Global 0.05Deg CMG, Version 061; global monthly NDVI and EVI fields.
- **Publisher:** NASA Land Processes Distributed Active Archive Center (LP DAAC).
- **CMR short name/version:** `MOD13C2` / `061`; confirmed by a live authenticated Earthaccess CMR granule search.
- **DOI:** [10.5067/MODIS/MOD13C2.061](https://doi.org/10.5067/MODIS/MOD13C2.061).
- **Observed source metadata:** NDVI and EVI are 3600×7200 int16 arrays at 0.05°. Metadata declares scale factor 10000, fill -3000, valid range -2000..10000. The quality layer ranks pixels; the ingest adapter retains rank 0 (good) and rank 1 (marginal), masks ranks 2–4 and aggregates blocks to a 2° analysis grid.
- **Actual granule inspected:** `MOD13C2.A2024001.061.2024038052740.hdf`, January 2024; downloaded from a real CMR granule link and decoded with HDF4. CMR returned 319 monthly granules for 2000-02 through 2026-08 in the live range query. The local ingest currently has a contiguous partial record; see `docs/PROGRESS.md` before treating its trend products as complete.
- **Variables:** `CMG 0.05 Deg Monthly NDVI` and `CMG 0.05 Deg Monthly EVI`, unitless indices. Each is a proxy affected by retrieval quality, clouds, snow/ice, atmosphere, view geometry, and land cover; neither is a direct measure of biomass.

## Other CMR-verified NASA products awaiting GES DISC authorization

`earthaccess.search_datasets` and actual granule searches confirmed the following short names, versions, DOI/collection metadata, and example granules. Real GET data requests returned HTTP 403 `EULA Acceptance Failure`; no downloaded values are used in the app yet.

| Product | CMR short name | Version | DOI | Status |
| --- | --- | --- | --- | --- |
| MERRA-2 monthly single-level flux diagnostics | `M2TMNXFLX` | 5.12.4 | [10.5067/0JRLVL8YV2Y4](https://doi.org/10.5067/0JRLVL8YV2Y4) | Awaiting GES DISC application EULA |
| GLDAS Noah monthly 0.25° | `GLDAS_NOAH025_M` | 2.1 | [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO) | Awaiting GES DISC application EULA |
| GPM IMERG Final monthly | `GPM_3IMERGM` | 07 | [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07) | Awaiting GES DISC application EULA |
| AIRS/Aqua monthly support product | `AIRS3STM` | 7.0 | [10.5067/UBENJB9D3T2H](https://doi.org/10.5067/UBENJB9D3T2H) | Awaiting GES DISC application EULA |
| OMI daily tropospheric NO₂ | `OMNO2d` | 004 | [10.5067/AURA/OMI/DATA3407](https://doi.org/10.5067/AURA/OMI/DATA3407) | Awaiting GES DISC application EULA |

The app catalog presents these as unavailable until the access agreement is accepted, variables and units are confirmed from actual product files, and the complete analysis pipeline has been run.

## NASA GIBS Blue Marble basemap

- **Layer:** `BlueMarble_NextGeneration`, titled “Blue Marble (MODIS)” in the live WMTS capabilities document.
- **Publisher/service:** NASA Global Imagery Browse Services (GIBS), WMTS EPSG:3857.
- **Tile service:** `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`
- **Verification:** WMTS GetCapabilities and a real tile request returned the layer and HTTP 200 on 2026-11-01.
- **Use:** Geographic reference background only. It is not an input to the trend calculation; all analytical values and overlays are generated from GISTEMP v4.
- **NASA documentation:** [GIBS Access Basics](https://nasa-gibs.github.io/gibs-api-docs/access-basics/) and [Blue Marble: Next Generation](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/).

### NASA GISTEMP published global monthly series (validation reference)

- **Product:** Land-Ocean Temperature Index global monthly mean anomalies.
- **Publisher:** NASA Goddard Institute for Space Studies.
- **URL:** [Global monthly CSV](https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts%2BdSST.csv), linked from the [official downloads page](https://data.giss.nasa.gov/gistemp/data_v4.html).
- **Accessed:** 2026-11-01.
- **Use:** Independent published aggregate for validating the processed gridded product; not used as an application input.
