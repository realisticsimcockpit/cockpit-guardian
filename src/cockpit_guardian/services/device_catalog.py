from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from ..models import DeviceKind
from .integration_notices import normalize_usb_id


CATALOG_ASSET = "device_catalog.json"


@dataclass(frozen=True, slots=True)
class CatalogMatch:
    name: str | None
    kind: DeviceKind


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    name: str | None
    kind: DeviceKind
    vid: str | None = None
    pid: str | None = None
    name_contains: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogEntry | None":
        try:
            kind = DeviceKind(str(data.get("kind") or DeviceKind.OTHER.value))
        except ValueError:
            return None
        needles = data.get("name_contains") or ()
        if isinstance(needles, str):
            needles = (needles,)
        return cls(
            name=str(data["name"]) if data.get("name") else None,
            kind=kind,
            vid=normalize_usb_id(data.get("vid")),
            pid=normalize_usb_id(data.get("pid")),
            name_contains=tuple(str(item).strip().lower() for item in needles if str(item).strip()),
        )

    def matches_usb(self, vid: str | None, pid: str | None) -> bool:
        return bool(self.vid and self.pid and self.vid == normalize_usb_id(vid) and self.pid == normalize_usb_id(pid))

    def matches_name(self, name: str | None) -> bool:
        normalized = (name or "").lower()
        return bool(normalized and any(needle in normalized for needle in self.name_contains))


class DeviceCatalog:
    def __init__(self, entries: list[CatalogEntry] | None = None) -> None:
        self.entries = entries or []

    @classmethod
    def load_default(cls) -> "DeviceCatalog":
        return cls.from_file(_catalog_asset_path())

    @classmethod
    def from_file(cls, path: Path) -> "DeviceCatalog":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return cls()
        return cls(_entries_from_data(data))

    @classmethod
    def from_files(cls, *paths: Path) -> "DeviceCatalog":
        entries: list[CatalogEntry] = []
        for path in paths:
            entries.extend(cls.from_file(path).entries)
        return cls(entries)

    def match(self, name: str | None, vid: str | None = None, pid: str | None = None) -> CatalogMatch | None:
        for entry in self.entries:
            if entry.matches_usb(vid, pid):
                return CatalogMatch(entry.name, entry.kind)
        for entry in self.entries:
            if entry.matches_name(name):
                return CatalogMatch(entry.name, entry.kind)
        return None


def ensure_user_catalog(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        shutil.copy2(_catalog_asset_path(), path)
    return path


def _entries_from_data(data: dict[str, Any]) -> list[CatalogEntry]:
    raw_entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(raw_entries, list):
        return []
    entries: list[CatalogEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            continue
        entry = CatalogEntry.from_dict(raw)
        if entry is not None:
            entries.append(entry)
    return entries


def _catalog_asset_path() -> Path:
    return Path(str(resources.files("cockpit_guardian.assets").joinpath(CATALOG_ASSET)))
