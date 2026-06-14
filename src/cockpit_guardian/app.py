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


STARTUP_STATUS_TEXT = {
    "en": {
        "start": "Starting Cockpit Guardian",
        "config": "Loading profile and backups",
        "windows": "Initializing Windows USB / HID / COM modules",
        "software": "Preparing SimHub and cockpit software detection",
        "interface": "Building dashboard interface",
        "scan": "Preparing first Windows scan",
        "ready": "Cockpit Guardian ready",
    },
    "fr": {
        "start": "Démarrage de Cockpit Guardian",
        "config": "Chargement du profil et des sauvegardes",
        "windows": "Initialisation des modules Windows USB / HID / COM",
        "software": "Préparation de SimHub et des logiciels cockpit",
        "interface": "Construction de l'interface tableau de bord",
        "scan": "Préparation du premier scan Windows",
        "ready": "Cockpit Guardian prêt",
    },
}


class StartupSplash(QWidget):
    def __init__(self, language: str = "en") -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setWindowTitle("Cockpit Guardian")
        self.setFixedSize(905, 679)
        self.setStyleSheet("background: #000000; color: #ffffff;")
        self._language = language if language in STARTUP_STATUS_TEXT else "en"
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
        self.status_label = QLabel(self)
        self.status_label.setObjectName("StartupStatus")
        self.status_label.setStyleSheet(
            "color: #ffffff; background: transparent; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;"
        )
        self.status_label.setText(self._status_text("start"))
        self.status_label.adjustSize()
        self._position_status_label()
        self.status_label.raise_()

    def show_and_start(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            self.move(screen_rect.center() - self.rect().center())
        self.show()
        if self._player:
            self._player.play()
        self.status_label.raise_()

    def set_status(self, key: str) -> None:
        self.status_label.setText(self._status_text(key))
        self.status_label.adjustSize()
        self._position_status_label()
        self.status_label.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._position_status_label()

    def _position_status_label(self) -> None:
        margin = 24
        self.status_label.move(margin, self.height() - self.status_label.height() - margin)

    def _status_text(self, key: str) -> str:
        return STARTUP_STATUS_TEXT[self._language].get(key, STARTUP_STATUS_TEXT[self._language]["start"])

    def finish(self) -> None:
        if self._player:
            self._player.stop()
        self.close()
        if self._asset_context is not None:
            self._asset_context.__exit__(None, None, None)
            self._asset_context = None


def startup_language() -> str:
    try:
        return ConfigManager(AppPaths()).load_settings().language
    except Exception:
        return "en"


def build_controller(status_callback=None) -> AppController:
    status = status_callback or (lambda _key: None)
    status("config")
    paths = AppPaths()
    config = ConfigManager(paths)
    logger = configure_logging(paths)
    status("windows")
    detector = DeviceDetector()
    joystick_manager = JoystickOrderManager()
    status("software")
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
    splash = StartupSplash(startup_language())
    splash.show_and_start()
    app.processEvents()
    controller = build_controller(lambda key: (splash.set_status(key), app.processEvents()))
    splash.set_status("interface")
    app.processEvents()
    window = MainWindow(controller)
    splash.set_status("scan")
    app.processEvents()
    window.show()
    splash.set_status("ready")
    app.processEvents()
    splash.finish()
    return app.exec()
