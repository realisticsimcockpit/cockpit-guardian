from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


VID_PID_RE = re.compile(r"VID_([0-9A-Fa-f]{4}).*PID_([0-9A-Fa-f]{4})")


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def parse_vid_pid(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    match = VID_PID_RE.search(text)
    if not match:
        return None, None
    return match.group(1).upper(), match.group(2).upper()


def hidden_subprocess_kwargs() -> dict[str, Any]:
    if not is_windows():
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }


def run_powershell_json(script: str, timeout: int = 12) -> list[dict[str, Any]]:
    if not is_windows():
        return []
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "$OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"{script} | ConvertTo-Json -Depth 5"
        ),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def relaunch_as_admin() -> bool:
    if not is_windows():
        return False
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    executable = sys.executable
    try:
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        return int(result) > 32
    except Exception:
        return False


def startup_shortcut_path(app_name: str = "Cockpit Guardian") -> Path | None:
    if not is_windows():
        return None
    startup = os.environ.get("APPDATA")
    if not startup:
        return None
    return Path(startup) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / f"{app_name}.lnk"
