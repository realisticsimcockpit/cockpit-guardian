from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .check_engine import CheckEngine
from .config_manager import ConfigManager
from .controller import AppController
from .logging_service import configure_logging
from .paths import AppPaths
from .services.com_manager import ComPortManager, UsbRescanService
from .services.device_detector import DeviceDetector
from .services.joystick_manager import JoystickOrderManager
from .services.restore_engine import RestoreEngine
from .services.simhub import SimHubIntegration
from .services.software_detector import SoftwareDetector
from .services.usb_health import UsbHealthMonitor
from .ui.main_window import MainWindow


def build_controller() -> AppController:
    paths = AppPaths()
    config = ConfigManager(paths)
    logger = configure_logging(paths)
    detector = DeviceDetector()
    joystick_manager = JoystickOrderManager()
    software_detector = SoftwareDetector()
    check_engine = CheckEngine(
        detector=detector,
        joystick_manager=joystick_manager,
        usb_health=UsbHealthMonitor(),
        software_detector=software_detector,
        simhub=SimHubIntegration(),
        logger=logger,
    )
    restore_engine = RestoreEngine(
        config=config,
        com_manager=ComPortManager(),
        joystick_manager=joystick_manager,
        usb_rescan=UsbRescanService(),
        logger=logger,
    )
    logger.info("Cockpit Guardian started")
    return AppController(
        config=config,
        check_engine=check_engine,
        restore_engine=restore_engine,
        detector=detector,
        joystick_manager=joystick_manager,
        software_detector=software_detector,
        logger=logger,
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Cockpit Guardian")
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(build_controller())
    window.show()
    return app.exec()
