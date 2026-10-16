"""Direct geometry validation endpoint."""

from fastapi import APIRouter

from ..geometry.engine import validate_geometry
from ..schemas import GeometryInput, ValidateResponse

router = APIRouter(prefix="/api/v1/parcels", tags=["parcels"])


@router.post("/validate", response_model=ValidateResponse)
def validate(payload: GeometryInput) -> ValidateResponse:
    result = validate_geometry(
        payload.model_dump(exclude={"crs"}),
        payload.crs,
    )
    return ValidateResponse(
        valid=result.valid,
        reason=result.reason,
        area_m2=result.area_m2,
        perimeter_m=result.perimeter_m,
        crs=result.crs,
        warnings=result.warnings,
    )