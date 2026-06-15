from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..models import CockpitDevice, DeviceBus, JoystickOrderResult
from .windows_util import hidden_subprocess_kwargs, is_windows


DIRECTINPUT_ROOT = r"System\CurrentControlSet\Control\MediaProperties\PrivateProperties\DirectInput"


@dataclass(slots=True)
class JoystickRegistrySlot:
    vid: str
    pid: str
    calibration_key: str
    registry_path: str
    current_id: int
    value_type: int


@dataclass(slots=True)
class JoystickRestoreAssignment:
    device: CockpitDevice
    slot: JoystickRegistrySlot
    desired_id: int


@dataclass(slots=True)
class JoystickOrderManager:
    """Reads and restores Windows DirectInput controller order."""

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

    def restore(
        self,
        expected: list[str],
        backup_path: Path,
        current_devices: list[CockpitDevice] | None = None,
    ) -> tuple[bool, str, bool]:
        if not expected:
            return True, "No saved joystick order to restore.", False
        if not is_windows():
            return False, "Joystick order restore is only available on Windows.", False

        try:
            assignments = self._plan_restore(expected, current_devices or [])
        except ValueError as exc:
            return False, f"Joystick order restore not safe: {exc}", False
        if not assignments:
            return True, "Joystick order already OK.", False

        registry_backup = self._export_directinput_registry_backup(backup_path)
        if registry_backup is None:
            return False, "Could not create DirectInput registry backup. No joystick order change was made.", False

        try:
            for assignment in assignments:
                self._write_joystick_id(assignment.slot, assignment.desired_id)
            self._notify_joystick_config_changed()
        except Exception as exc:
            return False, f"Could not restore joystick order: {exc}. Registry backup saved to {registry_backup}.", False

        ordered_names = ", ".join(assignment.device.label for assignment in sorted(assignments, key=lambda item: item.desired_id))
        return (
            True,
            f"Joystick order restored: {ordered_names}. Registry backup saved to {registry_backup}. Restart games that already had DirectInput devices open.",
            False,
        )

    def rollback_registry_backup(self, backup_path: Path) -> tuple[bool, str]:
        registry_backup = self._registry_backup_path(backup_path)
        if not registry_backup.exists():
            return True, "No joystick registry backup found for this restore."
        completed = subprocess.run(
            ["reg", "import", str(registry_backup)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            **hidden_subprocess_kwargs(),
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "DirectInput registry rollback failed."
            return False, message
        self._notify_joystick_config_changed()
        return True, f"Joystick registry restored from {registry_backup}."

    def _plan_restore(self, expected: list[str], current_devices: list[CockpitDevice]) -> list[JoystickRestoreAssignment]:
        hid_devices = [device for device in current_devices if device.bus == DeviceBus.HID and device.hid]
        by_label = self._devices_by_label(hid_devices)
        missing = [name for name in expected if name.lower() not in by_label]
        if missing:
            raise ValueError("missing current joystick(s): " + ", ".join(missing))

        full_order = list(expected)
        for device in sorted(hid_devices, key=lambda item: item.hid.joystick_order or 9999):
            if device.label not in full_order:
                full_order.append(device.label)

        slots_by_vid_pid: dict[tuple[str, str], list[JoystickRegistrySlot]] = {}
        assignments: list[JoystickRestoreAssignment] = []
        used_slots: set[str] = set()
        for desired_id, label in enumerate(full_order):
            device = by_label.get(label.lower())
            if not device or not device.hid or not device.hid.vid or not device.hid.pid:
                raise ValueError(f"{label} has no DirectInput VID/PID identity")
            key = (device.hid.vid.upper(), device.hid.pid.upper())
            if key not in slots_by_vid_pid:
                slots_by_vid_pid[key] = self._read_directinput_slots(*key)
            slot = self._slot_for_device(device, slots_by_vid_pid[key])
            if slot.registry_path in used_slots:
                raise ValueError(f"{device.label} maps to a DirectInput registry slot already used")
            used_slots.add(slot.registry_path)
            if slot.current_id != desired_id:
                assignments.append(JoystickRestoreAssignment(device=device, slot=slot, desired_id=desired_id))
        return assignments

    @staticmethod
    def _devices_by_label(devices: list[CockpitDevice]) -> dict[str, CockpitDevice]:
        by_label: dict[str, CockpitDevice] = {}
        duplicates: set[str] = set()
        for device in devices:
            label = device.label.lower()
            if label in by_label:
                duplicates.add(device.label)
            by_label[label] = device
        if duplicates:
            raise ValueError("duplicate joystick label(s): " + ", ".join(sorted(duplicates)))
        return by_label

    @staticmethod
    def _slot_for_device(device: CockpitDevice, slots: list[JoystickRegistrySlot]) -> JoystickRegistrySlot:
        if not slots:
            raise ValueError(f"{device.label} has no DirectInput calibration slot")
        current_id = (device.hid.joystick_order - 1) if device.hid and device.hid.joystick_order else None
        matches = [slot for slot in slots if slot.current_id == current_id]
        if len(matches) == 1:
            return matches[0]
        if current_id is None and len(slots) == 1:
            return slots[0]
        if len(slots) == 1 and not matches:
            return slots[0]
        raise ValueError(f"{device.label} has ambiguous DirectInput calibration slots")

    @staticmethod
    def _read_directinput_slots(vid: str, pid: str) -> list[JoystickRegistrySlot]:
        try:
            import winreg
        except Exception as exc:
            raise ValueError("winreg is unavailable") from exc

        base_path = rf"{DIRECTINPUT_ROOT}\VID_{vid.upper()}&PID_{pid.upper()}\Calibration"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_path) as base_key:
                slots: list[JoystickRegistrySlot] = []
                index = 0
                while True:
                    try:
                        calibration_key = winreg.EnumKey(base_key, index)
                    except OSError:
                        break
                    index += 1
                    registry_path = rf"{base_path}\{calibration_key}"
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as calibration:
                            value, value_type = winreg.QueryValueEx(calibration, "Joystick Id")
                    except FileNotFoundError:
                        continue
                    current_id = JoystickOrderManager._decode_joystick_id(value)
                    if current_id is None:
                        continue
                    slots.append(
                        JoystickRegistrySlot(
                            vid=vid.upper(),
                            pid=pid.upper(),
                            calibration_key=calibration_key,
                            registry_path=registry_path,
                            current_id=current_id,
                            value_type=value_type,
                        )
                    )
                return slots
        except FileNotFoundError as exc:
            raise ValueError(f"DirectInput registry key not found for VID_{vid}&PID_{pid}") from exc

    @staticmethod
    def _decode_joystick_id(value) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, bytes) and len(value) >= 4:
            return int.from_bytes(value[:4], "little")
        return None

    @staticmethod
    def _encode_joystick_id(value: int, value_type: int):
        try:
            import winreg
        except Exception:
            winreg = None
        if winreg is not None and value_type == winreg.REG_DWORD:
            return value
        return int(value).to_bytes(4, "little")

    @staticmethod
    def _write_joystick_id(slot: JoystickRegistrySlot, desired_id: int) -> None:
        try:
            import winreg
        except Exception as exc:
            raise ValueError("winreg is unavailable") from exc
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, slot.registry_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(
                key,
                "Joystick Id",
                0,
                slot.value_type,
                JoystickOrderManager._encode_joystick_id(desired_id, slot.value_type),
            )
            winreg.FlushKey(key)

    @staticmethod
    def _registry_backup_path(backup_path: Path) -> Path:
        return backup_path.with_suffix(".directinput.reg")

    def _export_directinput_registry_backup(self, backup_path: Path) -> Path | None:
        target = self._registry_backup_path(backup_path)
        completed = subprocess.run(
            ["reg", "export", rf"HKCU\{DIRECTINPUT_ROOT}", str(target), "/y"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            **hidden_subprocess_kwargs(),
        )
        return target if completed.returncode == 0 and target.exists() else None

    @staticmethod
    def _notify_joystick_config_changed() -> None:
        try:
            import ctypes

            ctypes.WinDLL("winmm").joyConfigChanged(0)
        except Exception:
            return
