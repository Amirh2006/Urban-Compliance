"""Registry that selects the correct adapter for a given file."""

from pathlib import Path

from .base import AdapterResult, FileAdapter
from .csv_adapter import CSVAdapter
from .geojson_adapter import GeoJSONAdapter

_ADAPTERS: list[FileAdapter] = [
    GeoJSONAdapter(),
    CSVAdapter(),
]


def get_adapter(path: Path) -> FileAdapter | None:
    """Return the first adapter that can handle the given path, if any."""
    for adapter in _ADAPTERS:
        if adapter.can_handle(path):
            return adapter
    return None


def parse_file(path: Path) -> AdapterResult:
    """Parse the file using the matching adapter or return an error result."""
    adapter = get_adapter(path)
    if adapter is None:
        return AdapterResult(
            ok=False, error=f"unsupported file extension: {path.suffix}"
        )
    return adapter.parse(path)