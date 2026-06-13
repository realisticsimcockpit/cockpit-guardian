import tempfile
import unittest

from cockpit_guardian.config_manager import ConfigManager
from cockpit_guardian.models import CockpitDevice, DeviceBus, DeviceKind, HidIdentity, Priority, Settings
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
            )

            config.create_snapshot("Rig", [device], [], ["Wheelbase"])
            loaded = config.load_snapshot()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.profile_name, "Rig")
        self.assertEqual(loaded.devices[0].kind, DeviceKind.WHEEL)
        self.assertEqual(loaded.devices[0].hid.vid, "1234")
        self.assertEqual(loaded.joystick_order, ["Wheelbase"])

    def test_backups_created_in_same_second_are_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))

            first = config.make_backup("restore")
            second = config.make_backup("restore")

            self.assertNotEqual(first.name, second.name)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())


if __name__ == "__main__":
    unittest.main()
