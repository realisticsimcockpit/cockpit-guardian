from __future__ import annotations

import os
from dataclasses import dataclass

from ..models import SoftwareState, SoftwareStatus


@dataclass(slots=True)
class SimHubStatus:
    available: bool
    ffb_clipping_percent: float | None = None
    message: str = "SimHub not available"


class SimHubIntegration:
    """Small integration point for SimHub data.

    SimHub setups vary by plugin and telemetry source. This class currently detects
    availability through software status and accepts an optional environment override
    for development/tests. A real SimHub plugin or local API adapter can be added
    here while preserving the rest of the application.
    """

    def get_status(self, software: list[SoftwareStatus]) -> SimHubStatus:
        simhub = next((item for item in software if item.name == "SimHub"), None)
        if not simhub or simhub.state != SoftwareState.RUNNING:
            return SimHubStatus(available=False)

        override = os.environ.get("COCKPIT_GUARDIAN_SIMHUB_FFB_CLIPPING")
        if override:
            try:
                clipping = float(override)
            except ValueError:
                clipping = None
        else:
            clipping = None
        if clipping is None:
            return SimHubStatus(available=True, message="SimHub available")
        return SimHubStatus(available=True, ffb_clipping_percent=clipping, message=f"FFB clipping {clipping:.0f}%")
