"""Adapter for GeoJSON files (.geojson, .json)."""

import json
from pathlib import Path

from .base import AdapterResult, FileAdapter


class GeoJSONAdapter(FileAdapter):
    """Read the first geometry found in a GeoJSON document."""

    name = "geojson"
    extensions = (".geojson", ".json")

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> AdapterResult:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return AdapterResult(ok=False, error=f"failed to read GeoJSON: {exc}")

        crs: str | None = None
        if isinstance(data, dict) and isinstance(data.get("crs"), dict):
            props = data["crs"].get("properties") or {}
            crs = props.get("name")

        geom: dict | None = None
        if isinstance(data, dict):
            if data.get("type") == "FeatureCollection":
                features = data.get("features") or []
                if not features:
                    return AdapterResult(ok=False, error="FeatureCollection is empty")
                geom = features[0].get("geometry")
            elif data.get("type") == "Feature":
                geom = data.get("geometry")
            else:
                geom = data

        if not isinstance(geom, dict) or "type" not in geom:
            return AdapterResult(ok=False, error="no valid geometry found in file")

        return AdapterResult(ok=True, geojson=geom, crs=crs)