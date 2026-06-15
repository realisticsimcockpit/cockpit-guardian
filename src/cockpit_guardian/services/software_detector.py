from __future__ import annotations

import platform
import re
import subprocess
import time
from dataclasses import dataclass, field

from ..models import SoftwareState, SoftwareStatus
from .windows_util import hidden_subprocess_kwargs, run_powershell_json


SOFTWARE_CATALOG: dict[str, dict[str, object]] = {
    "SimHub": {"process": ["SimHubWPF", "SimHub"], "display": ["SimHub"]},
    "CrewChief": {"process": ["CrewChiefV4", "CrewChief"], "display": ["CrewChief"]},
    "Moza Pit House": {
        "process": ["MOZA Pit House", "MOZAPitHouse"],
        "display": ["MOZA Pit House"],
    },
    "SimPro Manager": {
        "process": ["SimProManager", "SimProManager2", "SimProManager3"],
        "display": ["SimPro Manager", "SimProManager"],
    },
    "Pimax Play": {"process": ["PimaxClient", "PimaxPlay"], "display": ["Pimax Play"]},
    "Meta Quest Link": {
        "process": ["OculusClient", "OVRServer_x64", "MetaQuestLink"],
        "display": ["Meta Quest Link", "Meta Horizon Link", "Oculus"],
    },
    "Fanatec App": {
        "process": ["FanatecApp", "FanatecControlPanel", "FanaLab"],
        "display": ["Fanatec App", "Fanatec Driver", "Fanatec Control Panel", "FanaLab"],
    },
    "Simucube Tuner": {
        "process": ["SimucubeTuner", "TrueDrive"],
        "display": ["Simucube Tuner", "Simucube True Drive", "True Drive"],
    },
    "VNM Config": {
        "process": ["VNMConfig", "VNMSimCenter"],
        "display": ["VNM Config", "VNM Sim Center", "VNM Simulation"],
    },
    "VRS Wheel Tool": {
        "process": ["VRSWheelTool"],
        "display": ["VRS Wheel Tool", "VRS DirectForce Pro", "Virtual Racing School"],
    },
    "Thrustmaster": {
        "process": ["TARGETGUI", "TARGETScriptEditor", "Thrustmaster"],
        "display": ["Thrustmaster", "T.A.R.G.E.T", "TARGET"],
    },
    "PXN Racing": {
        "process": ["PXNRacing", "PXNWheel", "PXNSimRacing"],
        "display": ["PXN Racing", "PXN Wheel", "PXN SimRacing"],
    },
    "CONSPIT Link": {
        "process": ["CONSPITLink", "CONSPIT"],
        "display": ["CONSPIT Link", "CONSPIT"],
    },
    "OpenXR Companion": {"process": ["OpenXR-Companion"], "display": ["OpenXR Companion"]},
    "Stream Deck": {"process": ["StreamDeck"], "display": ["Stream Deck"]},
    "iRacing": {"process": ["iRacingSim64DX11", "iRacingUI"], "display": ["iRacing"]},
    "Assetto Corsa": {"process": ["acs", "AssettoCorsa"], "display": ["Assetto Corsa"]},
    "Assetto Corsa Competizione": {"process": ["AC2-Win64-Shipping", "AssettoCorsaCompetizione"], "display": ["Assetto Corsa Competizione"]},
    "Le Mans Ultimate": {"process": ["Le Mans Ultimate", "LMU"], "display": ["Le Mans Ultimate"]},
    "rFactor 2": {"process": ["rFactor2", "rFactor2 Dedicated"], "display": ["rFactor 2"]},
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
            installed_match = self._match_installed(display_names, installed)
            installed_path = installed_match or None
            is_required = name in required
            if is_running:
                state = SoftwareState.RUNNING
            elif installed_match is not None:
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
        best_score = -1
        best_path: str | None = None
        for installed_name, path in installed.items():
            for display_name in display_names:
                score = SoftwareDetector._installed_match_score(display_name, installed_name)
                if score > best_score:
                    best_score = score
                    best_path = path
        return best_path if best_score >= 0 else None

    @staticmethod
    def _installed_match_score(display_name: str, installed_name: str) -> int:
        display = display_name.lower().strip()
        installed = installed_name.lower().strip()
        normalized_display = SoftwareDetector._normalize_name(display)
        normalized_installed = SoftwareDetector._normalize_name(installed)
        if not display or not installed:
            return -1
        if installed == display or normalized_installed == normalized_display:
            score = 100
        elif re.search(rf"\b{re.escape(display)}\b", installed):
            score = 85
        elif installed.startswith(display) or normalized_installed.startswith(normalized_display):
            score = 70
        elif display in installed or normalized_display in normalized_installed:
            score = 50
        else:
            return -1
        if any(token in installed for token in ["driver", "screen", "plugin", "add-on", "addon", "sdk"]):
            score -= 35
        if " version " in installed or installed.startswith(f"{display} version"):
            score += 10
        return score

    @staticmethod
    def _normalize_name(value: str) -> str:
        return "".join(character for character in value.lower() if character.isalnum())
