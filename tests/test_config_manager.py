import json
import tempfile
import unittest
from pathlib import Path

from cockpit_guardian.config_manager import ConfigManager
from cockpit_guardian.models import CockpitDevice, DeviceBus, DeviceKind, HidIdentity, Priority, Settings, UsbConnectionInfo
from cockpit_guardian.paths import AppPaths


class ConfigManagerTests(unittest.TestCase):
    def test_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))
            settings = Settings(profile_name="Rig", ffb_clipping_threshold=14.0, simhub_required=True)
            config.save_settings(settings)

            loaded = config.load_settings()

        self.assertEqual(loaded.profile_name, "Rig")
        self.assertEqual(loaded.ffb_clipping_threshold, 14.0)
        self.assertIs(loaded.simhub_required, True)

    def test_snapshot_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))
            device = CockpitDevice(
                id="wheel-1",
                display_name="Wheelbase",
                kind=DeviceKind.WHEEL,
                bus=DeviceBus.HID,
                priority=Priority.REQUIRED,
                hid=HidIdentity(name="Wheelbase", vid="1234", pid="ABCD", joystick_order=1),
                usb=UsbConnectionInfo(label="USB 3.x capable path", usb_generation="USB 3.x", confidence="medium"),
            )

            config.create_snapshot("Rig", [device], [], ["Wheelbase"])
            loaded = config.load_snapshot()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.profile_name, "Rig")
        self.assertEqual(loaded.devices[0].kind, DeviceKind.WHEEL)
        self.assertEqual(loaded.devices[0].hid.vid, "1234")
        self.assertEqual(loaded.devices[0].usb.usb_generation, "USB 3.x")
        self.assertEqual(loaded.joystick_order, ["Wheelbase"])

    def test_backups_created_in_same_second_are_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))

            first = config.make_backup("restore")
            second = config.make_backup("restore")

            self.assertNotEqual(first.name, second.name)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_config_backup_export_import_roundtrip(self):
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as target_tmp:
            source = ConfigManager(AppPaths(source_tmp))
            target = ConfigManager(AppPaths(target_tmp))
            settings = Settings(profile_name="Cloud Rig", ffb_clipping_threshold=12.0, initial_deep_windows_scan_done=True)
            device = CockpitDevice(
                id="ddu-1",
                display_name="DDU",
                kind=DeviceKind.DDU,
                bus=DeviceBus.SERIAL,
                priority=Priority.REQUIRED,
            )
            source.save_settings(settings)
            source.create_snapshot("Cloud Rig", [device], [], [])
            backup_path = source.export_config_backup(Path(source_tmp) / "cloud_backup.json")

            target.import_config_backup(backup_path)
            imported_snapshot = target.load_snapshot()
            imported_settings = target.load_settings()

            self.assertIsNotNone(imported_snapshot)
            self.assertEqual(imported_snapshot.profile_name, "Cloud Rig")
            self.assertEqual(imported_snapshot.devices[0].display_name, "DDU")
            self.assertEqual(imported_settings.profile_name, "Cloud Rig")
            self.assertEqual(imported_settings.ffb_clipping_threshold, 12.0)
            self.assertFalse(imported_settings.initial_deep_windows_scan_done)

    def test_config_backup_export_requires_saved_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))

            with self.assertRaises(ValueError):
                config.export_config_backup(Path(tmp) / "missing_snapshot.json")

    def test_config_backup_contains_cloud_storage_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))
            config.create_snapshot("Cloud Rig", [], [], [])
            backup_path = config.export_config_backup(Path(tmp) / "backup.json")

            data = json.loads(backup_path.read_text(encoding="utf-8"))

            self.assertEqual(data["schema"], "cockpit_guardian.config_backup.v1")
            self.assertIn("cloud", data["recommended_storage"].lower())

    def test_invalid_config_backup_does_not_replace_current_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))
            config.create_snapshot("Current Rig", [], [], [])
            invalid_backup = Path(tmp) / "invalid.json"
            invalid_backup.write_text(
                json.dumps({"snapshot": {"devices": [{}]}, "settings": {"profile_name": "Bad Rig"}}),
                encoding="utf-8",
            )

            with self.assertRaises(KeyError):
                config.import_config_backup(invalid_backup)

            self.assertEqual(config.load_snapshot().profile_name, "Current Rig")


if __name__ == "__main__":
    unittest.main()
