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
    if variable != VARIABLE["id"]:
        raise HTTPException(status_code=404, detail="This MVP currently supports GISTEMP only.")


def _format_result(result: dict[str, object], label: str, source: str) -> dict[str, object]:
    trend = result["trend"]
    assert isinstance(trend, dict)
    result["variable"] = VARIABLE["id"]
    result["label"] = label
    result["source"] = source
    result["unit"] = VARIABLE["unit"]
    result["summary"] = make_summary(
        label,
        trend["slope_ols"],
        trend["slope_ols_lo"],
        trend["slope_ols_hi"],
        trend["p_ols"],
        trend["p_mk"],
        "K/year",
    )
    time_values = result.get("time", [])
    if time_values:
        result["period"] = {"start": time_values[0], "end": time_values[-1]}
    result["significant"] = bool(
        trend["p_ols"] is not None and trend["p_ols"] < 0.05
    )
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
    values: np.ndarray, dates: np.ndarray, label: str, source: str
) -> dict[str, object]:
    adjusted, seasonal = deseasonalize_monthly(values)
    result: dict[str, object] = {
        "time": dates.astype("datetime64[M]").astype(str).tolist(),
        "value": values.tolist(),
        "seasonal": seasonal.tolist(),
        "anomaly": adjusted.tolist(),
        "trend": analyze_series(adjusted),
    }
    return _format_result(result, label, source)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/variables", response_model=list[VariableInfo])
async def variables() -> list[dict[str, object]]:
    return [VARIABLE]


@app.get("/api/suggest", response_model=list[Suggestion])
async def suggest(theme: str = "climate", place: str = "") -> list[Suggestion]:
    if theme.lower() in {"climate", "temperature", "warming"}:
        return [
            Suggestion(
                variable=VARIABLE["id"],
                name=VARIABLE["name"],
                definition=VARIABLE["definition"],
                available=True,
                message=(
                    f"Start with monthly temperature anomalies for "
                    f"{place or 'your selected region'}."
                ),
            )
        ]
    return [
        Suggestion(
            variable=VARIABLE["id"],
            name=VARIABLE["name"],
            definition=VARIABLE["definition"],
            available=False,
            message=(
                "This first release analyzes temperature only; other themes are not yet "
                "available."
            ),
        )
    ]


@app.get("/api/regions", response_model=list[RegionDefinition])
async def regions() -> list[RegionDefinition]:
    return REGIONS


@app.post("/api/region", response_model=AnalysisResponse)
async def region_analysis(request: RegionRequest) -> dict[str, object]:
    _check_variable(request.variable)
    try:
        result = analyze_region(request.bounds, request.start, request.end, DATASET_PATH)
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _format_result(result, request.label, "NASA GISS GISTEMP v4")


@app.get("/api/point", response_model=AnalysisResponse)
async def point_analysis(
    variable: str = VARIABLE["id"],
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    start: str | None = None,
    end: str | None = None,
) -> dict[str, object]:
    _check_variable(variable)
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=503, detail="Processed GISTEMP data are not installed.")
    with xr.open_zarr(DATASET_PATH) as dataset:
        selected = dataset.temperature_anomaly.sel(lat=lat, lon=lon, method="nearest")
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
        "NASA GISS GISTEMP v4",
    )
    result["location"] = location
    return result


@app.get("/api/trend/{variable}", response_model=TrendMapResponse)
async def trend_layer(variable: str, window: str = "full") -> dict[str, object]:
    _check_variable(variable)
    if window not in VARIABLE["windows"]:
        raise HTTPException(status_code=422, detail="Unknown time window.")
    tile_dir = Path("data/tiles") / variable / window
    metadata_path = tile_dir / "palette.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=503, detail="Trend map is not precomputed yet.")
    import json

    metadata = json.loads(metadata_path.read_text())
    metadata["urls"] = {
        "slope": f"/tiles/{variable}/{window}/slope/{{z}}/{{x}}/{{y}}.png",
        "nonsignificant": f"/tiles/{variable}/{window}/nonsignificant/{{z}}/{{x}}/{{y}}.png",
    }
    return metadata


@app.get("/tiles/{variable}/{window}/{layer}/{z}/{x}/{y}.png")
async def map_tile(variable: str, window: str, layer: str, z: int, x: int, y: int) -> Response:
    _check_variable(variable)
    if window not in VARIABLE["windows"] or layer not in {"slope", "nonsignificant"}:
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
    format: Literal["csv", "png"] = "csv",
    west: float | None = None,
    south: float | None = None,
    east: float | None = None,
    north: float | None = None,
    start: str | None = None,
    end: str | None = None,
    window: str = "full",
    layer: str = "slope",
) -> Response:
    """Export a regional monthly series as CSV or a precomputed map layer as PNG."""
    _check_variable(variable)
    if format == "csv":
        coordinates = (west, south, east, north)
        if any(value is None for value in coordinates):
            raise HTTPException(
                status_code=422,
                detail="CSV export requires west, south, east, and north bounds.",
            )
        bounds = (west, south, east, north)
        try:
            series = analyze_region(bounds, start, end, DATASET_PATH)  # type: ignore[arg-type]
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        body = io.StringIO(newline="")
        writer = csv.writer(body)
        writer.writerow(["month", "value_K", "seasonal_cycle_K", "deseasonalized_anomaly_K"])
        writer.writerows(
            zip(series["time"], series["value"], series["seasonal"], series["anomaly"], strict=True)
        )
        return Response(
            content=body.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=gistemp-region.csv"},
        )

    if window not in VARIABLE["windows"] or layer not in {"slope", "nonsignificant"}:
        raise HTTPException(status_code=404, detail="Map export not found.")
    path = Path("data/tiles") / variable / window / f"{layer}.png"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Map export has not been generated.")
    return Response(
        content=path.read_bytes(),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=gistemp-{window}-{layer}.png"},
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
    left = await region_analysis(RegionRequest(bounds=lookup[a].bounds, label=lookup[a].name))
    right = await region_analysis(RegionRequest(bounds=lookup[b].bounds, label=lookup[b].name))
    return {"a": left, "b": right}
