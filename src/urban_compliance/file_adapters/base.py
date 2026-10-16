"""Base types shared by all file adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AdapterResult:
    """Outcome of running a file adapter on a specific file."""

    ok: bool
    geojson: dict | None = None
    crs: str | None = None
    error: str | None = None


class FileAdapter(ABC):
    """Common interface implemented by every supported file format adapter."""

    name: str = ""
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True when this adapter can process the given file."""

    @abstractmethod
    def parse(self, path: Path) -> AdapterResult:
        """Parse the file and return a normalized AdapterResult."""