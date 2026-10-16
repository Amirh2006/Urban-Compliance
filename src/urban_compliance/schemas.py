"""Pydantic request and response models for the API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parcel_code: str | None = Field(default=None, max_length=120)
    description: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parcel_code: str | None
    description: str | None
    created_at: datetime


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    size_bytes: int
    status: str
    error: str | None
    detected_crs: str | None
    created_at: datetime


class GeometryInput(BaseModel):
    type: str = "Polygon"
    coordinates: list[Any]
    crs: str | None = None


class ValidateResponse(BaseModel):
    valid: bool
    reason: str | None = None
    area_m2: float | None = None
    perimeter_m: float | None = None
    crs: str | None = None
    warnings: list[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    project_id: int
    file_id: int | None = None
    geometry: GeometryInput | None = None


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: str
    engine_version: str
    result: dict | None
    created_at: datetime