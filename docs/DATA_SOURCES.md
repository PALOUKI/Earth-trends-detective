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
