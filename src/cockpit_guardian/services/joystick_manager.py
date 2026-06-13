from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import CockpitDevice, DeviceBus, JoystickOrderResult
from .windows_util import is_admin, is_windows


@dataclass(slots=True)
class JoystickOrderManager:
    """Reads and restores Windows controller order.

    Windows stores game-controller ordering across DirectInput and registry-backed
    joystick mappings. The first implementation snapshots the device order exposed
    by detected HID devices and provides a safe restore hook. Native registry
    editing can be added here without changing UI code.
    """

    def read_current_order(self, devices: list[CockpitDevice]) -> list[str]:
        hid_devices = [device for device in devices if device.bus == DeviceBus.HID and device.hid]
        return [
            device.label
            for device in sorted(hid_devices, key=lambda item: item.hid.joystick_order or 9999)
        ]

    def compare(self, expected: list[str], current: list[str]) -> JoystickOrderResult:
        if not expected:
            return JoystickOrderResult(expected=[], current=current, ok=True, message="Joystick Order OK")
        ok = expected == current[: len(expected)]
        if ok:
            return JoystickOrderResult(expected=expected, current=current, ok=True, message="Joystick Order OK")
        return JoystickOrderResult(
            expected=expected,
            current=current,
            ok=False,
            restore_available=True,
            message="Joystick Order Changed - Restore Available",
        )

    def restore(self, expected: list[str], backup_path: Path) -> tuple[bool, str, bool]:
        if not expected:
            return True, "No saved joystick order to restore.", False
        if not is_windows():
            return False, "Joystick order restore is only available on Windows.", False
        if not is_admin():
            return False, "Administrator rights are required to restore joystick order.", True
        return (
            False,
            f"Joystick order backup saved to {backup_path}. No registry change was made because the Windows joystick-order adapter still requires hardware validation.",
            False,
        )
