from __future__ import annotations

import sys
from functools import lru_cache

from PySide6.QtCore import QObject, Qt, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QLabel, QStyleFactory, QVBoxLayout, QWidget

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
from .services.device_catalog import DeviceCatalog
from .services.device_detector import DeviceDetector
from .services.joystick_manager import JoystickOrderManager
from .services.restore_engine import RestoreEngine
from .services.software_detector import SoftwareDetector
from .services.telemetry import TelemetryService
from .services.usb_health import UsbHealthMonitor
from .services.usb_speed_scanner import USB_SPEED_SCAN_HELPER_ARG, run_usb_speed_scan_helper
from .services.usb_topology import UsbTopologyDetector
from .ui.assets import asset_icon, asset_path
from .ui.main_window import MainWindow


STARTUP_STATUS_TEXT = {
    "en": {
        "start": "Starting Cockpit Guardian",
        "config": "Loading profile and backups",
        "windows": "Initializing Windows USB / HID / COM modules",
        "software": "Preparing SimHub and cockpit software detection",
        "interface": "Building dashboard interface",
        "scan_usb": "Scan USB",
        "cockpit_checking": "Cockpit checking",
        "ready": "Cockpit Guardian ready",
        "startup_failed": "Startup scan failed",
    },
    "fr": {
        "start": "Démarrage de Cockpit Guardian",
        "config": "Chargement du profil et des sauvegardes",
        "windows": "Initialisation des modules Windows USB / HID / COM",
        "software": "Préparation de SimHub et des logiciels cockpit",
        "interface": "Construction de l'interface tableau de bord",
        "scan_usb": "Scan USB",
        "cockpit_checking": "Vérification cockpit",
        "ready": "Cockpit Guardian prêt",
        "startup_failed": "Echec du scan de démarrage",
    },
}

SPLASH_WIDTH = 1280
SPLASH_HEIGHT = 542
SPLASH_TEXT_COLOR = "#c8c8c8"
RETRO_FONT_CANDIDATES = ("Consolas", "Courier New", "Menlo", "Monaco", "Courier")


@lru_cache(maxsize=1)
def retro_font_family() -> str:
    available = set(QFontDatabase.families())
    return next((family for family in RETRO_FONT_CANDIDATES if family in available), "Courier")


class StartupSplash(QWidget):
    def __init__(self, language: str = "en") -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setWindowTitle("Cockpit Guardian")
        self.setFixedSize(SPLASH_WIDTH, SPLASH_HEIGHT)
        self.setStyleSheet(f"background: #000000; color: {SPLASH_TEXT_COLOR};")
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
            self._player.mediaStatusChanged.connect(self._media_status_changed)
        else:
            fallback = QLabel("COCKPIT GUARDIAN")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setFont(self._retro_font(11))
            fallback.setStyleSheet(f"color: {SPLASH_TEXT_COLOR}; letter-spacing: 1px;")
            layout.addWidget(fallback)
        self.status_label = QLabel(self)
        self.status_label.setObjectName("StartupStatus")
        self.status_label.setFont(self._retro_font(7))
        self.status_label.setStyleSheet(f"color: {SPLASH_TEXT_COLOR}; background: transparent; letter-spacing: 1.2px;")
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

    def _media_status_changed(self, status) -> None:
        if QMediaPlayer is None or self._player is None:
            return
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.pause()
            duration = self._player.duration()
            if duration > 0:
                self._player.setPosition(max(0, duration - 40))
            self.status_label.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._position_status_label()

    def _position_status_label(self) -> None:
        margin = 28
        self.status_label.move(margin, self.height() - self.status_label.height() - margin)

    def _status_text(self, key: str) -> str:
        return STARTUP_STATUS_TEXT[self._language].get(key, STARTUP_STATUS_TEXT[self._language]["start"]).upper()

    def _retro_font(self, point_size: int) -> QFont:
        font = QFont(retro_font_family())
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(point_size)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
        return font

    def finish(self) -> None:
        if self._player:
            self._player.stop()
        self.close()
        if self._asset_context is not None:
            self._asset_context.__exit__(None, None, None)
            self._asset_context = None


class StartupScanWorker(QObject):
    status_changed = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller

    @Slot()
    def run(self) -> None:
        try:
            self.status_changed.emit("scan_usb")
            self.controller.refresh_usb_speed_cache(force=False)
            self.status_changed.emit("cockpit_checking")
            self.controller.check_now()
            self.status_changed.emit("ready")
            self.finished.emit(self.controller)
        except Exception as exc:
            self.failed.emit(str(exc))


class StartupUiBridge(QObject):
    def __init__(
        self,
        splash: StartupSplash,
        startup_thread: QThread,
        controller: AppController,
        state: dict[str, object],
    ) -> None:
        super().__init__()
        self.splash = splash
        self.startup_thread = startup_thread
        self.controller = controller
        self.state = state

    @Slot(str)
    def set_status(self, key: str) -> None:
        self.splash.set_status(key)

    @Slot(object)
    def show_window(self, controller: AppController) -> None:
        window = MainWindow(controller, run_startup_checks=False)
        self.state["window"] = window
        window.show()
        self.splash.finish()
        self.startup_thread.quit()

    @Slot(str)
    def show_window_after_failure(self, message: str) -> None:
        self.controller.logger.warning("Startup scan failed: %s", message)
        self.splash.set_status("startup_failed")
        window = MainWindow(self.controller, run_startup_checks=True)
        self.state["window"] = window
        window.show()
        self.splash.finish()
        self.startup_thread.quit()


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
    user_catalog = config.ensure_device_catalog()
    logger = configure_logging(paths)
    status("windows")
    catalog = DeviceCatalog.from_file(user_catalog)
    if not catalog.entries:
        catalog = DeviceCatalog.load_default()
    detector = DeviceDetector(_catalog=catalog, _usb_topology=UsbTopologyDetector(speed_cache_path=paths.usb_speed_cache))
    joystick_manager = JoystickOrderManager()
    status("software")
    software_detector = SoftwareDetector()
    check_engine = CheckEngine(
        detector=detector,
        joystick_manager=joystick_manager,
        usb_health=UsbHealthMonitor(),
        software_detector=software_detector,
        telemetry_service=TelemetryService(),
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
    if USB_SPEED_SCAN_HELPER_ARG in sys.argv:
        return run_usb_speed_scan_helper()
    app = QApplication(sys.argv)
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    app.setApplicationName("Cockpit Guardian")
    app.setWindowIcon(asset_icon("app_icon_256.png"))
    app.setQuitOnLastWindowClosed(False)
    splash = StartupSplash(startup_language())
    splash.show_and_start()
    app.processEvents()
    controller = build_controller(lambda key: (splash.set_status(key), app.processEvents()))
    splash.set_status("interface")
    app.processEvents()
    state: dict[str, object] = {}
    startup_thread = QThread()
    startup_worker = StartupScanWorker(controller)
    startup_worker.moveToThread(startup_thread)
    startup_bridge = StartupUiBridge(splash, startup_thread, controller, state)

    startup_thread.started.connect(startup_worker.run)
    startup_worker.status_changed.connect(startup_bridge.set_status)
    startup_worker.finished.connect(startup_bridge.show_window)
    startup_worker.failed.connect(startup_bridge.show_window_after_failure)
    startup_worker.finished.connect(startup_worker.deleteLater)
    startup_worker.failed.connect(startup_worker.deleteLater)
    startup_thread.finished.connect(startup_thread.deleteLater)
    state["startup_thread"] = startup_thread
    state["startup_worker"] = startup_worker
    state["startup_bridge"] = startup_bridge
    startup_thread.start()
    return app.exec()
