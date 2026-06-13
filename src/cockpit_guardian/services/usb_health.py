from __future__ import annotations

import time
from dataclasses import dataclass

from ..models import Severity, UsbEvent, UsbHealthSummary, utc_now_iso
from .windows_util import run_powershell_json


USB_KEYWORDS = [
    "usb",
    "device not recognized",
    "enumeration",
    "reset",
    "disconnect",
    "timeout",
    "hub",
]


@dataclass(slots=True)
class UsbHealthMonitor:
    _cached_summary: UsbHealthSummary | None = None
    _cached_at: float = 0.0

    def check(self, cache_ttl_seconds: int = 120) -> UsbHealthSummary:
        now = time.monotonic()
        if self._cached_summary is not None and now - self._cached_at <= max(0, cache_ttl_seconds):
            return self._cached_summary
        rows = self._read_windows_events()
        events: list[UsbEvent] = []
        for row in rows:
            message = str(row.get("Message") or "")
            if not message or not any(keyword in message.lower() for keyword in USB_KEYWORDS):
                continue
            severity = self._severity(message)
            events.append(
                UsbEvent(
                    timestamp=str(row.get("TimeCreated") or utc_now_iso()),
                    severity=severity,
                    device_name=self._device_name(message),
                    message=self._shorten(message),
                    raw=message,
                )
            )
        if not events:
            self._cached_summary = UsbHealthSummary()
            self._cached_at = now
            return self._cached_summary

        critical_count = sum(1 for event in events if event.severity == Severity.CRITICAL)
        warning_count = sum(1 for event in events if event.severity == Severity.WARNING)
        stability_score = max(0, 100 - critical_count * 25 - warning_count * 10)
        if critical_count:
            severity = Severity.CRITICAL
            message = "USB Health : Critical - view details"
        else:
            severity = Severity.WARNING
            message = "USB Health : Warning - view details"
        self._cached_summary = UsbHealthSummary(severity=severity, message=message, events=events[:50], stability_score=stability_score)
        self._cached_at = now
        return self._cached_summary

    def _read_windows_events(self) -> list[dict]:
        script = (
            "Get-WinEvent -LogName System -MaxEvents 200 -ErrorAction SilentlyContinue | "
            "Where-Object { $_.ProviderName -match 'USB|Kernel-PnP|UserPnp' -or $_.Message -match 'USB|device not recognized|enumeration|hub' } | "
            "Select-Object TimeCreated, ProviderName, Id, LevelDisplayName, Message"
        )
        return run_powershell_json(script, timeout=15)

    @staticmethod
    def _severity(message: str) -> Severity:
        lower = message.lower()
        if "not recognized" in lower or "failed" in lower or "error" in lower:
            return Severity.CRITICAL
        return Severity.WARNING

    @staticmethod
    def _device_name(message: str) -> str:
        first_line = message.strip().splitlines()[0] if message.strip() else "USB device"
        return first_line[:80]

    @staticmethod
    def _shorten(message: str) -> str:
        compact = " ".join(message.split())
        return compact[:240]
