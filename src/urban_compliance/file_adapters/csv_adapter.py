"""Adapter for CSV files containing x/y coordinate columns."""

import csv
from pathlib import Path

from .base import AdapterResult, FileAdapter


class CSVAdapter(FileAdapter):
    """Build a polygon from x/y columns in a CSV file."""

    name = "csv"
    extensions = (".csv",)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> AdapterResult:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return AdapterResult(ok=False, error="CSV header row was not found")
                fields = {name.strip().lower() for name in reader.fieldnames}
                if not {"x", "y"} <= fields:
                    return AdapterResult(
                        ok=False, error="CSV must contain 'x' and 'y' columns"
                    )

                coords: list[list[float]] = []
                for row in reader:
                    x_raw = row.get("x") or row.get("X")
                    y_raw = row.get("y") or row.get("Y")
                    try:
                        coords.append([float(x_raw), float(y_raw)])  # type: ignore[arg-type]
                    except (TypeError, ValueError):
                        continue
        except Exception as exc:  # noqa: BLE001
            return AdapterResult(ok=False, error=f"failed to read CSV: {exc}")

        if len(coords) < 3:
            return AdapterResult(ok=False, error="at least three points are required")
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        return AdapterResult(
            ok=True,
            geojson={"type": "Polygon", "coordinates": [coords]},
        )