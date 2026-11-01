"""Storage and measured-field mapping for fully supported variables."""

from pathlib import Path

VARIABLE_CONFIG = {
    "gistemp_tas_anom": {
        "path": Path("data/processed/gistemp_tas_anom.zarr"),
        "field": "temperature_anomaly",
        "source": "NASA GISS GISTEMP v4",
        "unit": "K",
        "rate_unit": "K/year",
        "windows": ("full", "2010-fin", "2015-fin"),
    },
    "modis_ndvi": {
        "path": Path("data/processed/modis_ndvi.zarr"),
        "field": "ndvi_index",
        "source": "NASA Terra MODIS MOD13C2 v061, NDVI",
        "unit": "1",
        "rate_unit": "index/year",
        "windows": ("full", "2010-fin", "2015-fin"),
    },
    "modis_evi": {
        "path": Path("data/processed/modis_evi.zarr"),
        "field": "evi_index",
        "source": "NASA Terra MODIS MOD13C2 v061, EVI",
        "unit": "1",
        "rate_unit": "index/year",
        "windows": ("full", "2010-fin", "2015-fin"),
    },
}
