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

## Other CMR-verified NASA products after GES DISC authorization

Live authenticated CMR searches confirmed the short names, versions, and granules for all five products. Following Earthdata application authorization, each HTTPS link returned HTTP 206 for a real 4 KiB byte-range read from an actual data file. GPM, OMI, AIRS, MERRA-2, and GLDAS real sample files were downloaded and inspected; historical series are being acquired for daily OMI and monthly MERRA-2/GLDAS.

| Product | CMR short name | Version | DOI | Verified state |
| --- | --- | --- | --- | --- |
| MERRA-2 monthly single-level flux diagnostics | `M2TMNXFLX` | 5.12.4 | [10.5067/0JRLVL8YV2Y4](https://doi.org/10.5067/0JRLVL8YV2Y4) | January 2024 file field `EVAP`, units `kg m-2 s-1`; 2000-01–2009-12 monthly series downloading |
| GLDAS Noah monthly 0.25° | `GLDAS_NOAH025_M` | 2.1 | [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO) | January 2024 file field `SoilMoi0_10cm_inst`, units `kg m-2`; 2000-01–2009-12 monthly series downloading |
| GPM IMERG Final monthly | `GPM_3IMERGM` | 07 | [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07) | 309 real granules ingested; `Grid/precipitation`, mm/hr; trend grids and XYZ tiles generated for 2000-01–2025-09 |
| AIRS/Aqua monthly standard product | `AIRS3STM` | 7.0 | [10.5067/UBENJB9D3T2H](https://doi.org/10.5067/UBENJB9D3T2H) | Sample decoded; `SurfAirTemp_A` is surface atmospheric temperature, K, per NASA V7 L3 guide; 2002-09–2012-08 monthly series downloading |
| OMI daily tropospheric NO₂ | `OMNO2d` | 004 | [10.5067/AURA/OMI/DATA3407](https://doi.org/10.5067/AURA/OMI/DATA3407) | Sample decoded: `ColumnAmountNO2TropCloudScreened`, molec/cm²; daily-to-monthly aggregation pending |

Access authorization is now in place. Products remain unavailable for analysis in the interface until their source variables, local time series, trend statistics, and maps are fully checked and generated.

The AIRS entry is the standard monthly AIRS-only product. Its downloaded sample contains `SurfAirTemp_A` (ascending); the NASA V7 L3 User Guide identifies it as surface atmospheric temperature in kelvin and describes the 1° monthly grid. It is an atmosphere/climate variable, not an air-pollution measurement.

OMI is the air-quality candidate. NASA describes `OMNO2d` as a daily 0.25° L3 global grid and its field documentation identifies `ColumnAmountNO2TropCloudScreened` in molecules/cm²; the product is cloud-screened, not a surface monitor. See the [NASA OMNO2d V004 dataset record](https://data.nasa.gov/dataset/omi-aura-no2-cloud-screened-total-and-tropospheric-column-l3-global-gridded-0-25-degree-x--7a338) and [OMI README](https://ozoneaq.gsfc.nasa.gov/content/public/OMI/READMEs/README.OMNO2.pdf). Monthly values in this project are to be computed from the valid daily grids.

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
