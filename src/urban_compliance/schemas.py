"""Pydantic request and response models for the API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from .rules.evaluator import SUPPORTED_KINDS


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parcel_code: str | None = Field(default=None, max_length=120)
    description: str | None = None
    spatial_scope: str | None = Field(default=None, max_length=120)

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parcel_code: str | None
    description: str | None
    spatial_scope: str | None
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

class BuildingInput(BaseModel):
    """Optional building characteristics used to compute derived metrics."""

    height_m: float | None = Field(default=None, gt=0)
    footprint_m2: float | None = Field(default=None, gt=0)
    floors: int | None = Field(default=None, ge=1)
    setback_m: float | None = Field(default=None, ge=0)


class AnalysisRequest(BaseModel):
    project_id: int
    file_id: int | None = None
    geometry: GeometryInput | None = None
    building: BuildingInput | None = None


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
# Built from SUPPORTED_KINDS so this schema and the evaluator stay in sync:
# adding a new rule kind in one place updates both.
_KIND_PATTERN = "^(?:" + "|".join(SUPPORTED_KINDS) + ")$"


class RuleCreate(BaseModel):
    """Payload for creating a new rule."""

    code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    kind: str = Field(pattern=_KIND_PATTERN)
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


class KnowledgeSourceCreate(BaseModel):
    """Payload for creating a knowledge source."""

    title: str = Field(min_length=1, max_length=300)
    document_type: str | None = Field(default=None, max_length=80)
    document_number: str | None = Field(default=None, max_length=120)
    published_at: str | None = Field(default=None, max_length=40)
    effective_from: str | None = Field(default=None, max_length=40)
    version: str = Field(default="1.0.0", max_length=30)
    description: str | None = None
    is_verified: bool = False


class KnowledgeSourceOut(BaseModel):
    """Serialized knowledge source without its chunks."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    document_type: str | None
    document_number: str | None
    published_at: str | None
    effective_from: str | None
    version: str
    description: str | None
    filename: str | None
    size_bytes: int | None
    page_count: int
    extraction_status: str
    extraction_error: str | None
    is_verified: bool
    created_at: datetime


class KnowledgeChunkOut(BaseModel):
    """Serialized text chunk belonging to a source."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    page_number: int
    chunk_index: int
    text: str
    char_count: int


class KnowledgeSourceDetail(KnowledgeSourceOut):
    """Knowledge source with its extracted chunks."""

    chunks: list[KnowledgeChunkOut] = Field(default_factory=list)


class KnowledgeSearchHit(BaseModel):
    """A search hit pointing to a specific chunk."""

    chunk_id: int
    source_id: int
    source_title: str
    page_number: int
    chunk_index: int
    snippet: str