from __future__ import annotations

import csv
import io
import os
from pathlib import Path
from typing import Literal

import numpy as np
import xarray as xr
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api.app.schemas import (
    AnalysisResponse,
    ComparisonResponse,
    RegionDefinition,
    RegionRequest,
    Suggestion,
    TrendMapResponse,
    VariableInfo,
)
from api.app.summary import make_summary
from pipeline.regions import DATASET_PATH, analyze_region
from pipeline.trends.base import analyze_series, deseasonalize_monthly
from pipeline.trends.breakpoint import analyze_pettitt
from pipeline.variables import VARIABLE_CONFIG

load_dotenv()

VARIABLE = {
    "id": "gistemp_tas_anom",
    "name": "Surface temperature anomaly",
    "name_fr": "Anomalie de température de surface",
    "unit": "K",
    "definition": "Monthly difference from the 1951–1980 surface temperature mean.",
    "definition_fr": "Écart mensuel à la moyenne de température de surface de 1951–1980.",
    "period": "1880-present; monthly",
    "limitations": "Blended land and ocean anomalies; coverage varies by place and time.",
    "windows": ["full", "2010-fin", "2015-fin"],
}

CATALOG = [
    {
        **VARIABLE,
        "source": "NASA GISS GISTEMP v4",
        "doi": "10.1029/2023JD040179",
        "short_name": None,
        "status": "analysis_ready",
        "status_detail": "Source, regional analysis, and trend map are available.",
    },
    {
        "id": "modis_ndvi",
        "name": "MODIS monthly vegetation index (NDVI)",
        "name_fr": "Indice mensuel de végétation MODIS (NDVI)",
        "unit": "1",
        "definition": "Monthly MODIS normalized difference vegetation index.",
        "definition_fr": "Indice mensuel de végétation normalisé MODIS.",
        "period": "2000-02 onward; source sample verified, complete series not ingested",
        "limitations": (
            "Vegetation-index proxy; cloud, snow, viewing conditions and land cover "
            "affect retrievals."
        ),
        "windows": ["full"],
        "source": "NASA Terra MODIS MOD13C2 v061",
        "doi": "10.5067/MODIS/MOD13C2.061",
        "short_name": "MOD13C2",
        "status": "sample_downloaded",
        "status_detail": (
            "One real monthly granule is decoded; at least 120 consecutive months "
            "and trend products are still required."
        ),
    },
    {
        "id": "modis_evi",
        "name": "MODIS monthly enhanced vegetation index (EVI)",
        "name_fr": "Indice mensuel de végétation amélioré MODIS (EVI)",
        "unit": "1",
        "definition": "Monthly MODIS enhanced vegetation index.",
        "definition_fr": "Indice mensuel de végétation amélioré MODIS.",
        "period": "2000-02 onward; source sample verified, complete series not ingested",
        "limitations": (
            "Vegetation-index proxy; cloud, snow, viewing conditions and land cover "
            "affect retrievals."
        ),
        "windows": ["full"],
        "source": "NASA Terra MODIS MOD13C2 v061",
        "doi": "10.5067/MODIS/MOD13C2.061",
        "short_name": "MOD13C2",
        "status": "sample_downloaded",
        "status_detail": (
            "One real monthly granule is decoded; at least 120 consecutive months "
            "and trend products are still required."
        ),
    },
    {
        "id": "merra2_flux",
        "name": "MERRA-2 monthly flux diagnostics",
        "name_fr": "Diagnostics mensuels de flux MERRA-2",
        "unit": "Pending file-level verification",
        "definition": (
            "NASA MERRA-2 monthly surface-flux product; selected field and units "
            "await file inspection."
        ),
        "definition_fr": (
            "Produit NASA MERRA-2 mensuel de flux de surface ; variable et unités "
            "à confirmer sur le fichier."
        ),
        "period": "1980 onward",
        "limitations": "Model reanalysis, not a direct satellite measurement.",
        "source": "NASA GMAO MERRA-2 v5.12.4",
        "doi": "10.5067/0JRLVL8YV2Y4",
        "short_name": "M2TMNXFLX",
        "status": "acquiring",
        "status_detail": (
            "Earthdata links return real file bytes; field metadata and analysis products "
            "are pending."
        ),
    },
    {
        "id": "gldas_noah_monthly",
        "name": "GLDAS Noah monthly land-surface fields",
        "name_fr": "Variables mensuelles de surface terrestre GLDAS Noah",
        "unit": "Pending file-level verification",
        "definition": (
            "Monthly land-surface model output; selected field and units await file inspection."
        ),
        "definition_fr": (
            "Sortie mensuelle d'un modèle terrestre ; variable et unités à confirmer "
            "sur le fichier."
        ),
        "period": "2000 onward",
        "limitations": "Land-surface model output; not a direct satellite measurement.",
        "source": "NASA GLDAS Noah v2.1",
        "doi": "10.5067/SXAVCZFAQLNO",
        "short_name": "GLDAS_NOAH025_M",
        "status": "acquiring",
        "status_detail": (
            "Earthdata links return real file bytes; field metadata and analysis products "
            "are pending."
        ),
    },
    {
        "id": "gpm_precipitation",
        "name": "GPM IMERG monthly precipitation",
        "name_fr": "Précipitations mensuelles GPM IMERG",
        "unit": "mm/hr",
        "definition": "Monthly mean precipitation rate from the NASA GPM IMERG product.",
        "definition_fr": "Taux mensuel moyen de précipitations du produit NASA GPM IMERG.",
        "period": "2000-01 to 2025-09 in CMR; local processing pending",
        "limitations": (
            "Satellite precipitation estimates; uncertainty varies by surface and regime."
        ),
        "source": "NASA GPM IMERG v07",
        "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
        "short_name": "GPM_3IMERGM",
        "status": "acquiring",
        "status_detail": (
            "Earthdata access is verified; source files and analysis products "
            "are being prepared."
        ),
    },
    {
        "id": "airs_surface_air_temp",
        "name": "AIRS monthly surface air temperature",
        "name_fr": "Température de l'air en surface mensuelle AIRS",
        "unit": "K",
        "definition": (
            "NASA AIRS/Aqua monthly standard product field SurfAirTemp_A; unit and meaning "
            "verified against the NASA V7 L3 guide."
        ),
        "definition_fr": (
            "Température atmosphérique en surface mensuelle AIRS, champ SurfAirTemp_A ; unité K."
        ),
        "period": "2002 onward",
        "limitations": "Satellite retrieval; cloud clearing, coverage, and retrieval quality vary.",
        "source": "NASA AIRS/Aqua L3 Standard Physical Retrieval (AIRS-only) v7.0",
        "doi": "10.5067/UBENJB9D3T2H",
        "short_name": "AIRS3STM",
        "status": "sample_downloaded",
        "status_detail": (
            "A real monthly sample is downloaded; SurfAirTemp_A and K are verified, but "
            "a long time series and analysis products are not generated."
        ),
    },
    {
        "id": "omi_no2",
        "name": "OMI tropospheric nitrogen dioxide",
        "name_fr": "Dioxyde d'azote troposphérique OMI",
        "unit": "molec/cm2",
        "definition": "Cloud-screened tropospheric NO₂ column from NASA OMI daily Level-3 data.",
        "definition_fr": (
            "Colonne troposphérique de NO₂ filtrée des nuages issue du produit quotidien NASA OMI."
        ),
        "period": "2004 onward",
        "limitations": (
            "Satellite retrieval; cloud screening and row-anomaly flags affect spatial coverage."
        ),
        "source": "NASA Aura OMI Daily Level-3 v004",
        "doi": "10.5067/AURA/OMI/DATA3407",
        "short_name": "OMNO2d",
        "status": "acquiring",
        "status_detail": (
            "The measured field and units are verified from a real granule; daily-to-monthly "
            "aggregation and trend products are pending."
        ),
    },
]

REGIONS = [
    RegionDefinition(
        id="sahara",
        name="Sahara example box",
        name_fr="Rectangle d’exemple du Sahara",
        bounds=(-15.0, 15.0, 35.0, 32.0),
        description="An illustrative rectangular analysis area over the Sahara.",
        description_fr="Une emprise rectangulaire illustrative sur le Sahara.",
    ),
    RegionDefinition(
        id="amazon",
        name="Amazon example box",
        name_fr="Rectangle d’exemple de l’Amazonie",
        bounds=(-75.0, -15.0, -45.0, 5.0),
        description="An illustrative rectangular analysis area over the Amazon basin.",
        description_fr="Une emprise rectangulaire illustrative sur le bassin amazonien.",
    ),
    RegionDefinition(
        id="nile_delta",
        name="Nile Delta example box",
        name_fr="Rectangle d’exemple du delta du Nil",
        bounds=(28.0, 29.0, 33.0, 32.0),
        description="An illustrative rectangular analysis area around the Nile Delta.",
        description_fr="Une emprise rectangulaire illustrative autour du delta du Nil.",
    ),
    RegionDefinition(
        id="new_york",
        name="New York example box",
        name_fr="Rectangle d’exemple de New York",
        bounds=(-75.0, 39.0, -71.0, 42.0),
        description="An illustrative rectangular analysis area around New York City.",
        description_fr="Une emprise rectangulaire illustrative autour de New York.",
    ),
]

app = FastAPI(title="Earth Trends Detective", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _clean(value: object) -> object:
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(item) for item in value]
    if isinstance(value, np.floating | float):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def _check_variable(variable: str) -> None:
    if variable not in VARIABLE_CONFIG:
        raise HTTPException(status_code=404, detail="Unknown scientific variable.")


def _dataset_path(variable: str) -> Path:
    return DATASET_PATH if variable == "gistemp_tas_anom" else VARIABLE_CONFIG[variable]["path"]


def _format_result(
    result: dict[str, object], label: str, source: str, variable_id: str = "gistemp_tas_anom"
) -> dict[str, object]:
    config = VARIABLE_CONFIG[variable_id]
    trend = result["trend"]
    assert isinstance(trend, dict)
    time_values = result.get("time", [])
    anomalies = result.get("anomaly", [])
    if isinstance(time_values, list) and isinstance(anomalies, list):
        result["break"] = analyze_pettitt(np.asarray(anomalies, dtype=float), time_values)
    result["variable"] = variable_id
    result["label"] = label
    result["source"] = source
    result["unit"] = config["unit"]
    result["rate_unit"] = config["rate_unit"]
    result["summary"] = make_summary(
        label,
        trend["slope_ols"],
        trend["slope_ols_lo"],
        trend["slope_ols_hi"],
        trend["p_ols"],
        trend["p_mk"],
        config["rate_unit"],
        result.get("break"),
        str(config["name"]),
        str(config["name_fr"]),
    )
    if time_values:
        result["period"] = {"start": time_values[0], "end": time_values[-1]}
    result["significant"] = bool(trend["p_ols"] is not None and trend["p_ols"] < 0.05)
    result["caveats"] = [
        "Statistical association does not establish cause.",
        (
            "Mann-Kendall and Hamed-Rao test monotonic trend; Hamed-Rao can be unavailable "
            "for some series."
        ),
        "Regional bounds are rectangles and use cosine-latitude area weights.",
    ]
    return _clean(result)  # type: ignore[return-value]


def _from_values(
    values: np.ndarray,
    dates: np.ndarray,
    label: str,
    source: str,
    variable_id: str = "gistemp_tas_anom",
) -> dict[str, object]:
    adjusted, seasonal = deseasonalize_monthly(values)
    result: dict[str, object] = {
        "time": dates.astype("datetime64[M]").astype(str).tolist(),
        "value": values.tolist(),
        "seasonal": seasonal.tolist(),
        "anomaly": adjusted.tolist(),
        "trend": analyze_series(adjusted),
    }
    return _format_result(result, label, source, variable_id)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/variables", response_model=list[VariableInfo])
async def variables() -> list[dict[str, object]]:
    return [item for item in await catalog() if item["status"] == "analysis_ready"]


@app.get("/api/catalog")
async def catalog() -> list[dict[str, object]]:
    """Return verified scientific products and honest integration states."""
    records = [dict(item) for item in CATALOG]
    for item in records:
        config = VARIABLE_CONFIG.get(item["id"])
        if str(item["id"]).startswith("modis_"):
            raw_count = len(list(Path("data/raw/modis/mod13c2").glob("MOD13C2.A*.061.*.hdf")))
            if raw_count > 1:
                item["status"] = "acquiring"
                item["status_detail"] = (
                    f"{raw_count} candidate monthly granule files are present; validating, "
                    "preprocessing and trend products pending."
                )
        if config and _dataset_path(str(item["id"])).exists():
            with xr.open_zarr(_dataset_path(str(item["id"]))) as dataset:
                times = dataset.time.values
                if times.size:
                    first = np.datetime_as_string(times[0], unit="M")
                    last = np.datetime_as_string(times[-1], unit="M")
                    item["period"] = f"{first} to {last}; monthly"
            tile_meta = Path("data/tiles") / item["id"] / "full" / "palette.json"
            trend_data = Path("data/processed") / item["id"] / "trend_full.zarr"
            if tile_meta.is_file() and trend_data.exists():
                item["status"] = "analysis_ready"
                item["status_detail"] = "Time series, trend products, and map tiles are available."
            elif item["id"] != VARIABLE["id"]:
                item["status"] = "series_processed"
                item["status_detail"] = (
                    "Processed time series is available; trend maps are not generated yet."
                )
    return records


@app.get("/api/suggest", response_model=list[Suggestion])
async def suggest(theme: str = "climate", place: str = "") -> list[Suggestion]:
    normalized_place = place.strip().lower()
    region_match = next(
        (
            item
            for item in REGIONS
            if normalized_place
            and normalized_place in f"{item.id} {item.name} {item.name_fr}".lower()
        ),
        None,
    )
    if theme.lower() in {"climate", "temperature", "warming"}:
        return [
            Suggestion(
                variable=VARIABLE["id"],
                name=VARIABLE["name"],
                definition=VARIABLE["definition"],
                available=True,
                message=(
                    f"Start with monthly temperature anomalies for "
                    f"{region_match.name if region_match else place or 'your selected region'}."
                ),
                region_id=region_match.id if region_match else None,
            )
        ]
    catalog_by_theme = {
        "vegetation": "modis_ndvi",
        "plants": "modis_ndvi",
        "forest": "modis_ndvi",
        "water": "gpm_precipitation",
        "rainfall": "gpm_precipitation",
        "soil": "gldas_noah_monthly",
        "air": "omi_no2",
        "atmosphere": "airs_surface_air_temp",
        "air quality": "omi_no2",
    }
    candidate_id = catalog_by_theme.get(theme.lower())
    if candidate_id:
        candidate = next(item for item in await catalog() if item["id"] == candidate_id)
        ready = candidate["status"] == "analysis_ready"
        return [
            Suggestion(
                variable=str(candidate["id"]),
                name=str(candidate["name"]),
                definition=str(candidate["definition"]),
                available=ready,
                message=(
                    f"Analyze {candidate['name']} for {place or 'your selected region'}."
                    if ready
                    else str(candidate["status_detail"])
                ),
                region_id=region_match.id if region_match else None,
            )
        ]
    return [
        Suggestion(
            variable=VARIABLE["id"],
            name=VARIABLE["name"],
            definition=VARIABLE["definition"],
            available=False,
            message="No verified analysis-ready dataset is cataloged for this theme yet.",
            region_id=region_match.id if region_match else None,
        )
    ]


@app.get("/api/regions", response_model=list[RegionDefinition])
async def regions() -> list[RegionDefinition]:
    return REGIONS


@app.post("/api/region", response_model=AnalysisResponse)
async def region_analysis(request: RegionRequest) -> dict[str, object]:
    _check_variable(request.variable)
    config = VARIABLE_CONFIG[request.variable]
    dataset_path = _dataset_path(request.variable)
    if not dataset_path.exists():
        raise HTTPException(
            status_code=503,
            detail="This variable's processed time series is not installed.",
        )
    try:
        result = analyze_region(
            request.bounds,
            request.start,
            request.end,
            dataset_path,
            str(config["field"]),
        )
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _format_result(result, request.label, str(config["source"]), request.variable)


@app.get("/api/point", response_model=AnalysisResponse)
async def point_analysis(
    variable: str = VARIABLE["id"],
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    start: str | None = None,
    end: str | None = None,
) -> dict[str, object]:
    _check_variable(variable)
    config = VARIABLE_CONFIG[variable]
    dataset_path = _dataset_path(variable)
    if not dataset_path.exists():
        raise HTTPException(
            status_code=503,
            detail="This variable's processed time series is not installed.",
        )
    with xr.open_zarr(dataset_path) as dataset:
        selected = dataset[str(config["field"])].sel(lat=lat, lon=lon, method="nearest")
        if start:
            selected = selected.sel(time=slice(start, None))
        if end:
            selected = selected.sel(time=slice(None, end))
        values = np.asarray(selected.compute(scheduler="synchronous").values, dtype=float)
        dates = selected.time.values
        location = {"lat": float(selected.lat), "lon": float(selected.lon)}
    result = _from_values(
        values,
        dates,
        f"({location['lat']:.0f}°, {location['lon']:.0f}°)",
        str(config["source"]),
        variable,
    )
    result["location"] = location
    return result


@app.get("/api/trend/{variable}", response_model=TrendMapResponse)
async def trend_layer(variable: str, window: str = "full") -> dict[str, object]:
    _check_variable(variable)
    config = VARIABLE_CONFIG[variable]
    if window not in config["windows"]:
        raise HTTPException(status_code=422, detail="Unknown time window.")
    tile_dir = Path("data/tiles") / variable / window
    metadata_path = tile_dir / "palette.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=503, detail="Trend map is not precomputed yet.")
    import json

    metadata = json.loads(metadata_path.read_text())
    trend_path = Path("data/processed") / variable / f"trend_{window}.zarr"
    statistics: dict[str, float | int] = {}
    if trend_path.exists():
        with xr.open_zarr(trend_path) as trends:
            classes = np.asarray(trends.sign_class.values, dtype=float)
            valid = np.isfinite(np.asarray(trends.slope_ols.values, dtype=float))
            valid_count = int(valid.sum())
            statistics = {
                "valid_cells": valid_count,
                "significant_increase_cells": int(np.sum(classes == 1)),
                "significant_decrease_cells": int(np.sum(classes == -1)),
                "non_significant_cells": int(np.sum((classes == 0) & valid)),
            }
    metadata["statistics"] = statistics
    metadata["urls"] = {
        "slope": f"/tiles/{variable}/{window}/slope/{{z}}/{{x}}/{{y}}.png",
        "nonsignificant": f"/tiles/{variable}/{window}/nonsignificant/{{z}}/{{x}}/{{y}}.png",
    }
    return metadata


@app.get("/tiles/{variable}/{window}/{layer}/{z}/{x}/{y}.png")
async def map_tile(variable: str, window: str, layer: str, z: int, x: int, y: int) -> Response:
    _check_variable(variable)
    if window not in VARIABLE_CONFIG[variable]["windows"] or layer not in {
        "slope",
        "nonsignificant",
    }:
        raise HTTPException(status_code=404, detail="Map tile not found.")
    if not 0 <= z <= 5 or not 0 <= x < (1 << z) or not 0 <= y < (1 << z):
        raise HTTPException(status_code=404, detail="Map tile not found.")
    path = Path("data/tiles") / variable / window / layer / str(z) / str(x) / f"{y}.png"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Map tile has not been generated.")
    return Response(
        content=path.read_bytes(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=31536000"},
    )


@app.get("/api/export")
async def export_product(
    variable: str = VARIABLE["id"],
    format: Literal["csv", "png", "tif"] = "csv",
    west: float | None = None,
    south: float | None = None,
    east: float | None = None,
    north: float | None = None,
    start: str | None = None,
    end: str | None = None,
    window: str = "full",
    layer: str = "slope",
) -> Response:
    """Export a regional series as CSV or a precomputed map as PNG/GeoTIFF."""
    _check_variable(variable)
    config = VARIABLE_CONFIG[variable]
    if format == "csv":
        coordinates = (west, south, east, north)
        if any(value is None for value in coordinates):
            raise HTTPException(
                status_code=422,
                detail="CSV export requires west, south, east, and north bounds.",
            )
        bounds = (west, south, east, north)
        try:
            series = analyze_region(
                bounds,
                start,
                end,
                _dataset_path(variable),  # type: ignore[arg-type]
                str(config["field"]),
            )  # type: ignore[arg-type]
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        body = io.StringIO(newline="")
        writer = csv.writer(body)
        unit = str(config["unit"])
        writer.writerow(
            ["month", f"value_{unit}", f"seasonal_cycle_{unit}", f"deseasonalized_anomaly_{unit}"]
        )
        writer.writerows(
            zip(series["time"], series["value"], series["seasonal"], series["anomaly"], strict=True)
        )
        return Response(
            content=body.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={variable}-region.csv"},
        )

    if format == "tif":
        if window not in config["windows"]:
            raise HTTPException(status_code=404, detail="Map export not found.")
        path = Path("data/processed") / variable / f"trend_{window}.tif"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="GeoTIFF export has not been generated.")
        return Response(
            content=path.read_bytes(),
            media_type="image/tiff",
            headers={"Content-Disposition": f"attachment; filename={variable}-{window}.tif"},
        )

    if window not in config["windows"] or layer not in {"slope", "nonsignificant"}:
        raise HTTPException(status_code=404, detail="Map export not found.")
    path = Path("data/tiles") / variable / window / f"{layer}.png"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Map export has not been generated.")
    return Response(
        content=path.read_bytes(),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={variable}-{window}-{layer}.png"},
    )


@app.get("/api/compare", response_model=ComparisonResponse)
async def compare_regions(
    variable: str = VARIABLE["id"],
    a: str = "amazon",
    b: str = "sahara",
) -> dict[str, object]:
    _check_variable(variable)
    lookup = {item.id: item for item in REGIONS}
    if a not in lookup or b not in lookup:
        raise HTTPException(status_code=404, detail="Unknown predefined region.")
    left = await region_analysis(
        RegionRequest(variable=variable, bounds=lookup[a].bounds, label=lookup[a].name)
    )
    right = await region_analysis(
        RegionRequest(variable=variable, bounds=lookup[b].bounds, label=lookup[b].name)
    )
    return {"a": left, "b": right}
