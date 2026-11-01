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


class Suggestion(BaseModel):
    variable: str
    name: str
    definition: str
    available: bool
    message: str


class RegionDefinition(BaseModel):
    id: str
    name: str
    name_fr: str
    bounds: tuple[float, float, float, float]
    description: str
    description_fr: str
    geometry_type: Literal["illustrative_rectangle"] = "illustrative_rectangle"
