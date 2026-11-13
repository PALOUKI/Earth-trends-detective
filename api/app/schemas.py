from typing import Literal

from pydantic import BaseModel, Field


class RegionRequest(BaseModel):
    variable: str = "gistemp_tas_anom"
    bounds: tuple[float, float, float, float] = Field(
        description="west, south, east, north in EPSG:4326 degrees"
    )
    start: str | None = None
    end: str | None = None
    label: str = "Selected region"


class ExternalSeriesRequest(BaseModel):
    csv_text: str = Field(max_length=5_000_000)
    date_column: str = Field(min_length=1, max_length=120)
    value_column: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=80)
    unit: str = Field(min_length=1, max_length=40)


class CuahsiSearchRequest(BaseModel):
    bounds: tuple[float, float, float, float]
    start: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    keyword: str = Field(default="discharge", min_length=2, max_length=80)


class CuahsiAnalysisRequest(CuahsiSearchRequest):
    series_id: str = Field(min_length=1, max_length=300)


class VariableInfo(BaseModel):
    id: str
    name: str
    name_fr: str
    unit: str
    definition: str
    definition_fr: str
    period: str
    limitations: str
    windows: list[str]
    data_start: str | None = None
    data_end: str | None = None


class Suggestion(BaseModel):
    variable: str
    name: str
    definition: str
    available: bool
    message: str
    region_id: str | None = None


class RegionDefinition(BaseModel):
    id: str
    name: str
    name_fr: str
    bounds: tuple[float, float, float, float]
    description: str
    description_fr: str
    geometry_type: Literal["illustrative_rectangle"] = "illustrative_rectangle"


class TrendStatistics(BaseModel):
    n_valid: int
    slope_ols: float | None
    slope_ols_lo: float | None
    slope_ols_hi: float | None
    p_ols: float | None
    slope: float | None
    slope_lo: float | None
    slope_hi: float | None
    p_mk: float | None
    p_value: float | None


class SummaryText(BaseModel):
    en: str
    fr: str


class BreakResult(BaseModel):
    date: str
    p: float
    significant: bool
    statistic: float


class AnalysisResponse(BaseModel):
    variable: str
    label: str
    source: str
    unit: str
    rate_unit: str
    bounds: dict[str, float] | None = None
    location: dict[str, float] | None = None
    period: dict[str, str]
    time: list[str]
    value: list[float | None]
    seasonal: list[float | None]
    anomaly: list[float | None]
    trend: TrendStatistics
    break_result: BreakResult | None = Field(default=None, alias="break")
    significant: bool
    summary: SummaryText
    caveats: list[str]


class ComparisonResponse(BaseModel):
    a: AnalysisResponse
    b: AnalysisResponse


class TrendMapResponse(BaseModel):
    bounds: list[tuple[float, float]]
    slope_unit: str
    scale_min: float
    scale_max: float
    scale_percentile: float
    minzoom: int
    maxzoom: int
    tile_size: int
    tile_scheme: str
    palette: dict[str, str]
    layers: dict[str, str]
    interpretation: str
    statistics: dict[str, float | int] = Field(default_factory=dict)
    urls: dict[str, str] | None = None
