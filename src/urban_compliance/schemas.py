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

class ReportOut(BaseModel):
    """JSON report returned to clients for a completed analysis."""

    report_id: str
    report_version: str
    generated_at: str
    disclaimer: str
    project: dict[str, Any]
    analysis: dict[str, Any]
    summary: dict[str, Any]
    files: list[dict[str, Any]]
    tests: list[dict[str, Any]]
    warnings: list[str]
    review_items: list[str]
    assumptions: list[str]
    limitations: list[str]
    input_error: str | None = None
    rules_applied: list[Any] = Field(default_factory=list)
    sources: list[Any] = Field(default_factory=list)

class RuleCreate(BaseModel):
    """Payload for creating a new rule."""

    code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    kind: str = Field(pattern="^(min_area|max_area|min_perimeter)$")
    threshold: float
    source_reference: str | None = Field(default=None, max_length=300)
    document_number: str | None = Field(default=None, max_length=120)
    published_at: str | None = Field(default=None, max_length=40)
    effective_from: str | None = Field(default=None, max_length=40)
    version: str = Field(default="1.0.0", max_length=30)
    spatial_scope: str | None = Field(default=None, max_length=120)
    is_active: bool = True
    is_verified: bool = False
    description: str | None = None


class RuleOut(BaseModel):
    """Serialized rule returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    kind: str
    threshold: float
    source_reference: str | None
    document_number: str | None
    published_at: str | None
    effective_from: str | None
    version: str
    spatial_scope: str | None
    is_active: bool
    is_verified: bool
    description: str | None
    created_at: datetime