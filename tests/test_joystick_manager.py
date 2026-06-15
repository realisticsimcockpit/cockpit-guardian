from pathlib import Path

from cockpit_guardian.models import CockpitDevice, DeviceBus, DeviceKind, HidIdentity
from cockpit_guardian.services.joystick_manager import JoystickOrderManager, JoystickRegistrySlot


def _hid(label: str, vid: str, pid: str, order: int) -> CockpitDevice:
    return CockpitDevice(
        id=label.lower(),
        display_name=label,
        kind=DeviceKind.OTHER,
        bus=DeviceBus.HID,
        hid=HidIdentity(name=label, vid=vid, pid=pid, joystick_order=order),
    )


def test_restore_writes_directinput_ids_for_duplicate_vid_pid(monkeypatch, tmp_path):
    manager = JoystickOrderManager()
    current = [
        _hid("T.16000M (8714FD5)", "044F", "B10A", 3),
        _hid("T.16000M (1D8AD952)", "044F", "B10A", 6),
    ]
    slots = [
        JoystickRegistrySlot("044F", "B10A", "0", r"DirectInput\VID_044F&PID_B10A\Calibration\0", 5, 3),
        JoystickRegistrySlot("044F", "B10A", "1", r"DirectInput\VID_044F&PID_B10A\Calibration\1", 2, 3),
    ]
    writes = []
    backup = tmp_path / "restore.json"
    registry_backup = tmp_path / "restore.directinput.reg"
    registry_backup.write_text("backup", encoding="utf-8")

    monkeypatch.setattr("cockpit_guardian.services.joystick_manager.is_windows", lambda: True)
    monkeypatch.setattr(JoystickOrderManager, "_read_directinput_slots", staticmethod(lambda vid, pid: slots))
    monkeypatch.setattr(JoystickOrderManager, "_export_directinput_registry_backup", lambda self, path: registry_backup)
    monkeypatch.setattr(JoystickOrderManager, "_write_joystick_id", staticmethod(lambda slot, desired_id: writes.append((slot.calibration_key, desired_id))))
    monkeypatch.setattr(JoystickOrderManager, "_notify_joystick_config_changed", staticmethod(lambda: None))

    ok, message, requires_admin = manager.restore(["T.16000M (1D8AD952)", "T.16000M (8714FD5)"], backup, current)

    assert ok is True
    assert requires_admin is False
    assert "Joystick order restored" in message
    assert writes == [("0", 0), ("1", 1)]


def test_restore_refuses_missing_current_joystick(monkeypatch, tmp_path):
    manager = JoystickOrderManager()
    monkeypatch.setattr("cockpit_guardian.services.joystick_manager.is_windows", lambda: True)

    ok, message, _ = manager.restore(["Wheel"], Path(tmp_path) / "restore.json", [])

    assert ok is False
    assert "missing current joystick" in message


def test_decode_joystick_id_accepts_binary_and_dword():
    assert JoystickOrderManager._decode_joystick_id((7).to_bytes(4, "little")) == 7
    assert JoystickOrderManager._decode_joystick_id(3) == 3
