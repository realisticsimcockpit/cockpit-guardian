from __future__ import annotations

import mmap
import os
import struct
from collections import deque
from dataclasses import dataclass, field

from ..models import SoftwareState, SoftwareStatus, TelemetryStatus
from .windows_util import is_windows


IRACING_MEMMAP_NAME = r"Local\IRSDKMemMapFileName"
ASSETTO_PHYSICS_MEMMAP_NAME = r"Local\acpmf_physics"
RFACTOR2_TELEMETRY_MEMMAP_NAME = r"$rFactor2SMMP_Telemetry$"
FFB_CLIP_SIGNAL_PERCENT = 98.0


@dataclass(slots=True)
class TelemetryService:
    _ffb_windows: dict[str, deque[bool]] = field(default_factory=dict)
    window_size: int = 120

    def get_status(self, software: list[SoftwareStatus] | None = None) -> TelemetryStatus:
        software = software or []
        override = self._read_override()
        if override.available:
            return override

        for reader in (self._read_iracing, self._read_assetto, self._read_lmu):
            status = reader()
            if status.available:
                return status

        simhub = self._software(software, "SimHub")
        if simhub and simhub.state == SoftwareState.RUNNING:
            return TelemetryStatus(
                source="SimHub",
                available=True,
                message="SimHub running; no FFB clipping feed configured yet",
            )
        return TelemetryStatus()

    @staticmethod
    def _software(software: list[SoftwareStatus], name: str) -> SoftwareStatus | None:
        return next((item for item in software if item.name == name), None)

    @staticmethod
    def _read_override() -> TelemetryStatus:
        for env_name, source in (
            ("COCKPIT_GUARDIAN_FFB_CLIPPING", "Telemetry override"),
            ("COCKPIT_GUARDIAN_SIMHUB_FFB_CLIPPING", "SimHub override"),
        ):
            value = os.environ.get(env_name)
            if value is None:
                continue
            try:
                clipping = float(value)
            except ValueError:
                return TelemetryStatus(source=source, available=True, message=f"{env_name} is not numeric")
            return TelemetryStatus(
                source=source,
                available=True,
                message=f"FFB clipping {clipping:.0f}%",
                ffb_clipping_percent=clipping,
                raw_value=clipping,
            )
        return TelemetryStatus()

    def _read_iracing(self) -> TelemetryStatus:
        data = self._read_named_mmap(IRACING_MEMMAP_NAME, (16 * 1024 * 1024, 8 * 1024 * 1024, 4 * 1024 * 1024, 2 * 1024 * 1024, 1024 * 1024))
        if data is None:
            return TelemetryStatus()
        return self._parse_iracing(data)

    def _parse_iracing(self, data: bytes) -> TelemetryStatus:
        if not self._iracing_connected(data):
            return TelemetryStatus()
        signal = self._iracing_var_float(data, "SteeringWheelPctTorque")
        if signal is None:
            return TelemetryStatus(source="iRacing", available=True, message="iRacing telemetry available; FFB torque variable not present")
        return self._status_from_signal("iRacing", abs(signal) * 100.0, signal)

    @staticmethod
    def _iracing_connected(data: bytes) -> bool:
        if len(data) < 48:
            return False
        try:
            version, status = struct.unpack_from("<2i", data, 0)
        except struct.error:
            return False
        return version >= 1 and bool(status & 1)

    @staticmethod
    def _iracing_var_float(data: bytes, name: str) -> float | None:
        if len(data) < 112:
            return None
        try:
            (
                version,
                status,
                _tick_rate,
                _session_info_update,
                _session_info_len,
                _session_info_offset,
                num_vars,
                var_header_offset,
                num_buf,
                buf_len,
                _pad1,
                _pad2,
            ) = struct.unpack_from("<12i", data, 0)
        except struct.error:
            return None
        if version < 1 or not (status & 1) or not (0 < num_vars < 4096) or not (0 < num_buf <= 4):
            return None
        if var_header_offset <= 0 or buf_len <= 0:
            return None

        latest_tick = -1
        latest_offset = -1
        for index in range(num_buf):
            try:
                tick_count, buf_offset = struct.unpack_from("<2i", data, 48 + index * 16)
            except struct.error:
                continue
            if tick_count > latest_tick and 0 <= buf_offset < len(data):
                latest_tick = tick_count
                latest_offset = buf_offset
        if latest_offset < 0:
            return None

        header_size = 144
        for index in range(num_vars):
            offset = var_header_offset + index * header_size
            if offset + header_size > len(data):
                return None
            try:
                var_type, var_offset, count, _count_as_time, var_name, _desc, _unit = struct.unpack_from("<iii?3x32s64s32s", data, offset)
            except struct.error:
                return None
            decoded_name = var_name.split(b"\0", 1)[0].decode("ascii", errors="ignore")
            if decoded_name != name:
                continue
            if var_type != 4 or count < 1:
                return None
            value_offset = latest_offset + var_offset
            if value_offset + 4 > len(data):
                return None
            try:
                return float(struct.unpack_from("<f", data, value_offset)[0])
            except struct.error:
                return None
        return None

    def _read_assetto(self) -> TelemetryStatus:
        data = self._read_named_mmap(ASSETTO_PHYSICS_MEMMAP_NAME, (4096, 8192, 16384))
        if data is None or self._looks_empty(data):
            return TelemetryStatus()
        final_ff = self._assetto_final_ff(data)
        if final_ff is None:
            return TelemetryStatus(source="Assetto Corsa", available=True, message="Assetto shared memory available; FFB value not decoded")
        return self._status_from_signal("Assetto Corsa", abs(final_ff) * 100.0, final_ff)

    @staticmethod
    def _assetto_final_ff(data: bytes) -> float | None:
        offset_text = os.environ.get("COCKPIT_GUARDIAN_ASSETTO_FINAL_FF_OFFSET")
        if not offset_text:
            return None
        try:
            offset = int(offset_text, 0)
            return float(struct.unpack_from("<f", data, offset)[0])
        except (ValueError, struct.error):
            return None

    def _read_lmu(self) -> TelemetryStatus:
        data = self._read_named_mmap(RFACTOR2_TELEMETRY_MEMMAP_NAME, (8 * 1024 * 1024, 4 * 1024 * 1024, 1024 * 1024))
        if data is None or self._looks_empty(data):
            return TelemetryStatus()
        return TelemetryStatus(
            source="Le Mans Ultimate / rFactor 2",
            available=True,
            message="LMU/rF2 shared memory available; FFB clipping decoder pending",
        )

    def _status_from_signal(self, source: str, signal_percent: float, raw_value: float) -> TelemetryStatus:
        clipped = signal_percent >= FFB_CLIP_SIGNAL_PERCENT
        window = self._ffb_windows.setdefault(source, deque(maxlen=self.window_size))
        window.append(clipped)
        clipping_percent = 100.0 * sum(1 for item in window if item) / len(window)
        if clipped:
            message = f"FFB signal {signal_percent:.0f}% - clipping now"
        else:
            message = f"FFB signal {signal_percent:.0f}%"
        return TelemetryStatus(
            source=source,
            available=True,
            message=message,
            ffb_clipping_percent=clipping_percent,
            ffb_signal_percent=signal_percent,
            raw_value=raw_value,
        )

    @staticmethod
    def _looks_empty(data: bytes) -> bool:
        return not any(data[:256])

    @staticmethod
    def _read_named_mmap(name: str, candidate_sizes: tuple[int, ...]) -> bytes | None:
        if not is_windows():
            return None
        for size in candidate_sizes:
            try:
                with mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ) as mapped:
                    return mapped[:]
            except Exception:
                continue
        return None
