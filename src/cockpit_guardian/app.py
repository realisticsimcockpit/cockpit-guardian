from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PySide6.QtMultimediaWidgets import QVideoWidget
except Exception:  # pragma: no cover - depends on local Qt multimedia backend
    QAudioOutput = None
    QMediaPlayer = None
    QVideoWidget = None

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
from .ui.assets import asset_icon, asset_path
from .ui.main_window import MainWindow


class StartupSplash(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setWindowTitle("Cockpit Guardian")
        self.setFixedSize(905, 679)
        self.setStyleSheet("background: #000000; color: #ffffff;")
        self._asset_context = None
        self._player = None
        self._audio = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if QMediaPlayer is not None and QVideoWidget is not None and QAudioOutput is not None:
            video = QVideoWidget()
            video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            layout.addWidget(video)
            self._asset_context = asset_path("splash_screen.mp4")
            path = self._asset_context.__enter__()
            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._audio.setMuted(True)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(video)
            self._player.setSource(QUrl.fromLocalFile(str(path)))
            if hasattr(self._player, "setLoops"):
                self._player.setLoops(QMediaPlayer.Loops.Infinite)
        else:
            fallback = QLabel("COCKPIT GUARDIAN")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("font-size: 28px; font-weight: 800; color: #ffffff;")
            layout.addWidget(fallback)

    def show_and_start(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            self.move(screen_rect.center() - self.rect().center())
        self.show()
        if self._player:
            self._player.play()

    def finish(self) -> None:
        if self._player:
            self._player.stop()
        self.close()
        if self._asset_context is not None:
            self._asset_context.__exit__(None, None, None)
            self._asset_context = None


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
    app.setWindowIcon(asset_icon("app_icon_256.png"))
    app.setQuitOnLastWindowClosed(False)
    splash = StartupSplash()
    splash.show_and_start()
    app.processEvents()
    window = MainWindow(build_controller())
    window.show()
    splash.finish()
    return app.exec()
