from __future__ import annotations

import platform
import subprocess
import time
from dataclasses import dataclass, field

from ..models import SoftwareState, SoftwareStatus
from .windows_util import hidden_subprocess_kwargs, run_powershell_json


SOFTWARE_CATALOG: dict[str, dict[str, object]] = {
    "SimHub": {"process": ["SimHubWPF", "SimHub"], "display": ["SimHub"]},
    "CrewChief": {"process": ["CrewChiefV4", "CrewChief"], "display": ["CrewChief"]},
    "Moza Pit House": {"process": ["MOZA Pit House", "MOZAPitHouse"], "display": ["MOZA Pit House"]},
    "SimPro Manager": {"process": ["SimProManager"], "display": ["SimPro Manager"]},
    "Pimax Play": {"process": ["PimaxClient", "PimaxPlay"], "display": ["Pimax Play"]},
    "OpenXR Companion": {"process": ["OpenXR-Companion"], "display": ["OpenXR Companion"]},
    "Stream Deck": {"process": ["StreamDeck"], "display": ["Stream Deck"]},
}


@dataclass(slots=True)
class SoftwareDetector:
    _installed_cache: dict[str, str] = field(default_factory=dict)
    _installed_cache_at: float = 0.0

    def detect(self, required: set[str] | None = None, installed_cache_ttl_seconds: int = 300) -> list[SoftwareStatus]:
        required = required or set()
        running = self._running_processes()
        installed = self._installed_programs(cache_ttl_seconds=installed_cache_ttl_seconds)
        statuses: list[SoftwareStatus] = []
        for name, spec in SOFTWARE_CATALOG.items():
            process_names = [str(item).lower() for item in spec["process"]]
            display_names = [str(item).lower() for item in spec["display"]]
            is_running = any(proc in running for proc in process_names)
            installed_path = self._match_installed(display_names, installed)
            is_required = name in required
            if is_running:
                state = SoftwareState.RUNNING
            elif installed_path:
                state = SoftwareState.INSTALLED_CLOSED
            elif is_required:
                state = SoftwareState.REQUIRED_MISSING
            else:
                state = SoftwareState.NOT_DETECTED
            statuses.append(
                SoftwareStatus(
                    name=name,
                    state=state,
                    path=installed_path,
                    process_name=str(spec["process"][0]),
                    required=is_required,
                )
            )
        return statuses

    def _running_processes(self) -> set[str]:
        if platform.system() == "Windows":
            try:
                completed = subprocess.run(
                    ["tasklist", "/fo", "csv", "/nh"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    **hidden_subprocess_kwargs(),
                )
            except Exception:
                return set()
            names = set()
            for line in completed.stdout.splitlines():
                if not line.strip():
                    continue
                name = line.split(",", 1)[0].strip('"').rsplit(".", 1)[0].lower()
                names.add(name)
            return names
        return set()

    def _installed_programs(self, cache_ttl_seconds: int = 300) -> dict[str, str]:
        now = time.monotonic()
        if self._installed_cache and now - self._installed_cache_at <= max(0, cache_ttl_seconds):
            return dict(self._installed_cache)
        script = (
            "$paths = @("
            "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); "
            "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
            "Where-Object { $_.DisplayName } | "
            "Select-Object DisplayName, DisplayVersion, InstallLocation"
        )
        rows = run_powershell_json(script, timeout=15)
        installed: dict[str, str] = {}
        for row in rows:
            name = str(row.get("DisplayName") or "").lower()
            location = str(row.get("InstallLocation") or "")
            if name:
                installed[name] = location
        self._installed_cache = dict(installed)
        self._installed_cache_at = now
        return installed

    @staticmethod
    def _match_installed(display_names: list[str], installed: dict[str, str]) -> str | None:
        for installed_name, path in installed.items():
            if any(display_name in installed_name for display_name in display_names):
                return path or None
        return None
