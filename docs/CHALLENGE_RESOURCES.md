# NASA Space Apps Challenge resources

Copied from the challenge Resources tab by the project owner on 2026-11-13. NASA's disclaimer on the tab states that NASA does not endorse non-U.S. Government entities and that participants must follow the data-use parameters of non-U.S. Government websites.

## NASA Data & Resources

| Resource | Official URL | Intended relevance to this project |
| --- | --- | --- |
| Giovanni | https://giovanni.gsfc.nasa.gov/giovanni/ | NASA GES DISC tool for exploring Earth science variables, generating area-averaged time series, and downloading data. Use as an independent comparison where the same source variable, time range, region, units, and averaging are available. |
| Hydrology Time Series | https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series | NASA GES DISC hydrology time-series resource. Inspect its supported products and workflow before selecting it as a validation or demonstration source. |
| AppEEARS | https://appeears.earthdatacloud.nasa.gov/ | NASA tool to access and transform geospatial data from federal archives, including time-series generation. Potential data access/inspection resource; it is not automatically a validation oracle for this project's statistics. |
| NOAA Climate Data Online | https://www.ncei.noaa.gov/cdo-web/ | NOAA archive and discovery tools for historical station weather and climate data. A possible independent station-data comparison, subject to spatial representativeness and product/method differences. |
| SeaWiFS chlorophyll time-series article | https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf | NASA-hosted paper demonstrating regional remotely sensed chlorophyll time-series and significance analysis, with cautions about coastal retrieval confounders. Potential background for an aquatic/coastal use case, not a source dataset integrated by this project. |

## Space Agency Partner Resources

| Resource | Official URL | Intended relevance to this project |
| --- | --- | --- |
| KNMI Climate Explorer | https://climexp.knmi.nl/ | External scientific climate analysis and visualization tool. Potential comparison/context resource; check its access controls and exact dataset/method before citing a result. |
| Statistical test methods to detect trends | https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b | Secondary educational article on trend tests. Background reading only; statistical implementation and claims should rely on methods documentation and primary references. |
| A Comprehensive Guide to Statistical Significance | https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance | General educational article. Background reading only; it is not a primary Earth-science statistics reference. |
| GEO.ca | https://geo.ca/fr/accueil/ | Canadian open geospatial data discovery portal. Potential source discovery for Canada-focused work; any dataset must be individually checked for provenance, license, and time coverage. |
| RADARSAT Constellation Mission data | https://donnees-data.asc-csa.gc.ca/en/dataset/rcm | Canadian Space Agency data portal entry for RCM. Potential SAR imagery source, but not yet assessed for a time-series variable suitable for this analysis. |
| SWOT mission | https://www.asc-csa.gc.ca/eng/satellites/swot/ | Mission information for the NASA/CNES-led SWOT mission with CSA and UK Space Agency participation. Data integration would require selecting and verifying an actual accessible product and variable. |
| Monitoring and protecting ecosystems from space | https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp | CSA background article on satellite ecosystem monitoring; contextual reading, not a dataset record. |
| Synthetic Aperture Radar Python tutorial | https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial | CSA tutorial repository for working with RADARSAT imagery using Python/QGIS. Potential technical reference if SAR is later selected; not currently part of the supported data pipeline. |

## Use and verification notes

- The owner supplied the URLs above. They were opened/checked on 2026-11-13; a live page load alone does not verify that a product, API endpoint, collection, or dataset is suitable for this application.
- Giovanni's current interface and NASA documentation describe area-averaged time series and downloadable series. A search for the literal term `GISTEMP` returning no dataset does not by itself establish that Giovanni validation is impossible. First identify matching Giovanni products for the variables actually in the app and compare a small number of compatible cases. Record exact dataset identifiers, region, period, units, spatial weighting, missing-data handling, and the differences in preprocessing. If no compatible match exists, document the attempted queries and the concrete mismatch.
- CUAHSI is an optional hydrology data discovery direction mentioned in `AGENT_BRIEF.md`; it is not one of the supplied NASA challenge-tab resources. The resource page now includes HydroClient alongside NASA/NOAA sources and accepts downloaded series through the shared monthly-series analysis path. Its station observations remain identified as station records, not NASA data or gridded regional means.
- These resources do not change the project's current product readiness by themselves. Check `data/catalog.yaml`, processed files, and the live API before claiming a product is analysis-ready.
