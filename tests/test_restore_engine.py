import logging
import tempfile
import unittest

from cockpit_guardian.config_manager import ConfigManager
from cockpit_guardian.models import CheckReport, GlobalStatus, RestoreReport, utc_now_iso
from cockpit_guardian.paths import AppPaths
from cockpit_guardian.services.com_manager import ComPortManager, UsbRescanService
from cockpit_guardian.services.joystick_manager import JoystickOrderManager
from cockpit_guardian.services.restore_engine import RestoreEngine


class RestoreEngineTests(unittest.TestCase):
    def test_restore_noop_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(AppPaths(tmp))
            engine = RestoreEngine(
                config=config,
                com_manager=ComPortManager(),
                joystick_manager=JoystickOrderManager(),
                usb_rescan=UsbRescanService(),
                logger=logging.getLogger("test"),
            )
            report = CheckReport(timestamp=utc_now_iso(), global_status=GlobalStatus.COCKPIT_READY)

            result = engine.restore(report, None)

            self.assertIsInstance(result, RestoreReport)
            self.assertIs(result.success, True)
            self.assertIsNotNone(result.backup_path)
            self.assertIsNotNone(config.latest_backup())


if __name__ == "__main__":
    unittest.main()
