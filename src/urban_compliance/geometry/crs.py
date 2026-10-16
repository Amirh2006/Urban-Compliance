"""Helpers around pyproj CRS parsing and classification."""

from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError


def parse_crs(value: str | None) -> CRS | None:
    """Parse a user-supplied CRS string into a pyproj CRS object.

    Returns ``None`` when the value is missing or cannot be parsed.
    """
    if not value:
        return None
    try:
        return CRS.from_user_input(value)
    except CRSError:
        return None


def is_projected(crs: CRS | None) -> bool:
    """Return True when the CRS uses projected (metric) coordinates."""
    return crs is not None and crs.is_projected


def transformer(src: str, dst: str) -> Transformer:
    """Build a transformer between two CRS definitions (always_xy=True)."""
    return Transformer.from_crs(src, dst, always_xy=True)


def unit_name(crs: CRS | None) -> str | None:
    """Return the unit name of the first axis, if any."""
    if crs is None or not crs.axis_info:
        return None
    return crs.axis_info[0].unit_name