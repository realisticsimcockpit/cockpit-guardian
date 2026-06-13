from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from . import __version__
from .models import Settings, Snapshot, settings_from_dict, snapshot_from_dict, to_plain, utc_now_iso
from .paths import AppPaths


CONFIG_BACKUP_SCHEMA = "cockpit_guardian.config_backup.v1"


class ConfigManager:
    def __init__(self, paths: AppPaths | None = None) -> None:
        self.paths = paths or AppPaths()
        self.paths.ensure()

    def load_settings(self) -> Settings:
        if not self.paths.settings.exists():
            settings = Settings()
            self.save_settings(settings)
            return settings
        data = self._read_json(self.paths.settings)
        return settings_from_dict(data)

    def save_settings(self, settings: Settings) -> None:
        self._write_json(self.paths.settings, to_plain(settings))

    def load_snapshot(self) -> Snapshot | None:
        if not self.paths.snapshot.exists():
            return None
        return snapshot_from_dict(self._read_json(self.paths.snapshot))

    def save_snapshot(self, snapshot: Snapshot) -> None:
        self._write_json(self.paths.snapshot, to_plain(snapshot))

    def create_snapshot(self, profile_name: str, devices, software, joystick_order) -> Snapshot:
        snapshot = Snapshot(
            snapshot_date=utc_now_iso(),
            profile_name=profile_name,
            app_version=__version__,
            devices=list(devices),
            software=list(software),
            joystick_order=list(joystick_order),
        )
        self.save_snapshot(snapshot)
        return snapshot

    def make_backup(self, label: str, payload: dict[str, Any] | None = None) -> Path:
        stamp = utc_now_iso().replace(":", "-")
        backup_path = self.paths.backups / f"{stamp}_{label}.json"
        suffix = 1
        while backup_path.exists():
            suffix += 1
            backup_path = self.paths.backups / f"{stamp}_{label}_{suffix}.json"
        data: dict[str, Any] = {
            "created_at": utc_now_iso(),
            "label": label,
            "snapshot": None,
            "settings": None,
            "payload": payload or {},
        }
        if self.paths.snapshot.exists():
            data["snapshot"] = self._read_json(self.paths.snapshot)
        if self.paths.settings.exists():
            data["settings"] = self._read_json(self.paths.settings)
        self._write_json(backup_path, data)
        return backup_path

    def rollback_backup(self, backup_path: Path) -> None:
        data = self._read_json(backup_path)
        if data.get("snapshot") is not None:
            self._write_json(self.paths.snapshot, data["snapshot"])
        if data.get("settings") is not None:
            self._write_json(self.paths.settings, data["settings"])

    def latest_backup(self) -> Path | None:
        backups = sorted(self.paths.backups.glob("*.json"), key=lambda item: item.stat().st_mtime)
        return backups[-1] if backups else None

    def default_config_backup_name(self, profile_name: str | None = None) -> str:
        safe_profile = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in (profile_name or "cockpit").strip()
        ).strip("_")
        if not safe_profile:
            safe_profile = "cockpit"
        stamp = utc_now_iso().replace(":", "-")
        return f"cockpit_guardian_{safe_profile}_{stamp}.json"

    def export_config_backup(self, target: Path) -> Path:
        snapshot = self.load_snapshot()
        if snapshot is None:
            raise ValueError("No saved configuration found. Use Save Configuration first.")
        settings = self.load_settings()
        bundle = {
            "schema": CONFIG_BACKUP_SCHEMA,
            "exported_at": utc_now_iso(),
            "app_version": __version__,
            "recommended_storage": "Store this file in a cloud-synced folder before reinstalling Windows.",
            "snapshot": to_plain(snapshot),
            "settings": to_plain(settings),
        }
        self._write_json(target, bundle)
        return target

    def import_config_backup(self, source: Path) -> Path:
        bundle = self._read_json(source)
        snapshot_data = bundle.get("snapshot")
        settings_data = bundle.get("settings")
        if snapshot_data is None:
            raise ValueError("This file does not contain a Cockpit Guardian snapshot.")

        snapshot = snapshot_from_dict(snapshot_data)
        settings = settings_from_dict(settings_data) if settings_data is not None else None
        backup = self.make_backup("before_config_import", payload={"source": str(source)})
        self.save_snapshot(snapshot)
        if settings is not None:
            self.save_settings(settings)
        return backup

    def export_logs(self, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.paths.log_file.exists():
            shutil.copy2(self.paths.log_file, target)
        else:
            target.write_text("", encoding="utf-8")
        return target

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
