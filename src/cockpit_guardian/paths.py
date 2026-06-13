from __future__ import annotations

import os
import platform
from pathlib import Path


APP_NAME = "Cockpit Guardian"


def user_data_dir() -> Path:
    override = os.environ.get("COCKPIT_GUARDIAN_HOME")
    if override:
        return Path(override).expanduser()

    if platform.system() == "Windows":
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_NAME
    return Path.home() / ".cockpit_guardian"


class AppPaths:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else user_data_dir()
        self.logs = self.root / "logs"
        self.backups = self.root / "backups"
        self.exports = self.root / "exports"
        self.snapshot = self.root / "snapshot.json"
        self.settings = self.root / "settings.json"
        self.restore_history = self.root / "restore_history.json"

    def ensure(self) -> None:
        for path in [self.root, self.logs, self.backups, self.exports]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def log_file(self) -> Path:
        return self.logs / "cockpit_guardian.log"
