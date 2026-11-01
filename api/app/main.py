from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import xarray as xr
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api.app.schemas import RegionDefinition, RegionRequest, Suggestion
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
        trend["p_value"],
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


@app.get("/api/variables")
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


@app.post("/api/region")
async def region_analysis(request: RegionRequest) -> dict[str, object]:
    _check_variable(request.variable)
    try:
        result = analyze_region(request.bounds, request.start, request.end, DATASET_PATH)
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _format_result(result, request.label, "NASA GISS GISTEMP v4")


@app.get("/api/point")
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


@app.get("/api/trend/{variable}")
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
        "slope": f"/api/maps/{variable}/{window}/slope.png",
        "nonsignificant": f"/api/maps/{variable}/{window}/nonsignificant.png",
    }
    return metadata


@app.get("/api/maps/{variable}/{window}/{layer}.png")
async def map_image(variable: str, window: str, layer: str) -> Response:
    _check_variable(variable)
    if window not in VARIABLE["windows"] or layer not in {"slope", "nonsignificant"}:
        raise HTTPException(status_code=404, detail="Map layer not found.")
    path = Path("data/tiles") / variable / window / f"{layer}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Map layer has not been generated.")
    return Response(
        content=path.read_bytes(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/api/compare")
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
