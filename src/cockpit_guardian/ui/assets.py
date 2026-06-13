from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator

from PySide6.QtGui import QIcon, QPixmap


@contextmanager
def asset_path(name: str) -> Iterator[Path]:
    resource = files("cockpit_guardian.assets").joinpath(name)
    with as_file(resource) as path:
        yield path


def asset_icon(name: str) -> QIcon:
    with asset_path(name) as path:
        pixmap = QPixmap(str(path))
    return QIcon(pixmap)
