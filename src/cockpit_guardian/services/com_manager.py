from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import CockpitDevice
from .windows_util import is_admin, is_windows


@dataclass(slots=True)
class ComPortManager:
    """Restores expected COM port names for serial cockpit devices."""

    def restore_port(self, expected: CockpitDevice, detected: CockpitDevice, backup_path: Path) -> tuple[bool, str, bool]:
        expected_com = expected.serial.current_com if expected.serial else None
        current_com = detected.serial.current_com if detected.serial else None
        if not expected_com or not current_com or expected_com == current_com:
            return True, f"{expected.label} COM port already OK.", False
        if not is_windows():
            return False, "COM restore is only available on Windows.", False
        if not is_admin():
            return False, f"Administrator rights are required to restore {expected.label} to {expected_com}.", True
        try:
            self._set_windows_port_name(detected, expected_com)
        except NotImplementedError as exc:
            return False, f"{exc} Backup saved to {backup_path}.", False
        except Exception as exc:
            return False, f"Could not restore {expected.label}: {exc}", False
        return True, f"{expected.label} restored from {current_com} to {expected_com}.", False

    def _set_windows_port_name(self, detected: CockpitDevice, expected_com: str) -> None:
        if not detected.serial or not detected.serial.device_instance_id:
            raise NotImplementedError("Missing device instance ID for COM restore.")
        try:
            import winreg
        except Exception as exc:
            raise NotImplementedError("winreg is unavailable; cannot modify COM registry mapping.") from exc

        instance_id = detected.serial.device_instance_id
        registry_path = f"SYSTEM\\CurrentControlSet\\Enum\\{instance_id}\\Device Parameters"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "PortName", 0, winreg.REG_SZ, expected_com)
        except FileNotFoundError as exc:
            raise NotImplementedError(f"Registry path not found for {instance_id}.") from exc


@dataclass(slots=True)
class UsbRescanService:
    def rescan(self) -> tuple[bool, str, bool]:
        if not is_windows():
            return False, "USB rescan is only available on Windows.", False
        if not is_admin():
            return False, "Administrator rights are required for USB rescan.", True
        import subprocess

        completed = subprocess.run(["pnputil", "/scan-devices"], capture_output=True, text=True, timeout=30, check=False)
        if completed.returncode == 0:
            return True, "USB device rescan completed.", False
        return False, completed.stderr.strip() or completed.stdout.strip() or "USB rescan failed.", False
