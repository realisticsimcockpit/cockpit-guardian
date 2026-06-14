from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..controller import AppController
from ..models import CheckReport, DeviceBus, DeviceKind, GlobalStatus, Priority, RestoreReport, Settings, Severity, SoftwareState, to_plain
from .assets import asset_icon, asset_pixmap
from .theme import SEVERITY_COLORS, STATUS_COLORS, app_stylesheet
from .tray import GuardianTray
from ..services.integration_notices import INTEGRATION_NOTICES


WINDOW_WIDTH = 905
WINDOW_HEIGHT = 679
YOUTUBE_URL = "https://www.youtube.com/@realisticsimcockpit"
CHECKLIST_ROWS_PER_COLUMN = 8
CHECKLIST_COLUMNS = 3

DASHBOARD_TEXT = {
    "en": {
        "logo_credit": "by REALISTIC SIMCOCKPIT",
        "footer_prefix": "Author:",
        "footer_version": "Version",
        "status_labels": {
            GlobalStatus.CHECK_NOT_DONE: "Check Not Done",
            GlobalStatus.COCKPIT_READY: "Cockpit Ready",
            GlobalStatus.WARNING: "Warning",
            GlobalStatus.RESTORE_NEEDED: "Restore Needed",
            GlobalStatus.CRITICAL_DEVICE_MISSING: "Critical Device Missing",
        },
        "severity_labels": {
            Severity.OK: "OK",
            Severity.INFO: "Info",
            Severity.WARNING: "Warning",
            Severity.RESTORE_NEEDED: "Restore Needed",
            Severity.CRITICAL: "Critical",
        },
        "device_kinds": {
            DeviceKind.WHEEL: "Wheel",
            DeviceKind.PEDALS: "Pedals",
            DeviceKind.SHIFTER: "Shifter",
            DeviceKind.HANDBRAKE: "Handbrake",
            DeviceKind.BUTTON_BOX: "Button Box",
            DeviceKind.DDU: "DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Wind Simulator",
            DeviceKind.OTHER: "Other",
        },
        "checklist_device_kinds": {
            DeviceKind.WHEEL: "Wheel base",
            DeviceKind.PEDALS: "Pedals",
            DeviceKind.SHIFTER: "Shifter",
            DeviceKind.HANDBRAKE: "Handbrake",
            DeviceKind.BUTTON_BOX: "Button box",
            DeviceKind.DDU: "DDU display",
            DeviceKind.ARDUINO_SIMHUB: "SimHub Arduino",
            DeviceKind.WIND_SIMULATOR: "Wind",
            DeviceKind.OTHER: "Device",
        },
        "software_group": "Software",
        "unknown": "Unknown",
        "detected_com_status": "{com} detected",
        "com_mismatch_status": "Expected {expected}, detected {detected}",
        "missing_device": "Missing",
        "com_ports": "COM Ports",
        "save": "Save",
        "check": "Check",
        "restore": "Restore",
        "rollback": "Rollback",
        "export": "Export",
        "import": "Import",
        "device_headers": ["Device", "Role", "Status", "USB"],
        "joystick_order": "Joystick Order",
        "joystick_headers": ["#", "Joystick", "USB"],
        "usb_health": "USB",
        "tabs": ["Dashboard", "USB Health", "Logs", "Settings", "Advanced"],
    },
    "fr": {
        "logo_credit": "par REALISTIC SIMCOCKPIT",
        "footer_prefix": "Auteur :",
        "footer_version": "Version",
        "status_labels": {
            GlobalStatus.CHECK_NOT_DONE: "Contrôle non effectué",
            GlobalStatus.COCKPIT_READY: "Cockpit prêt",
            GlobalStatus.WARNING: "Avertissement",
            GlobalStatus.RESTORE_NEEDED: "Restauration requise",
            GlobalStatus.CRITICAL_DEVICE_MISSING: "Périphérique critique absent",
        },
        "severity_labels": {
            Severity.OK: "OK",
            Severity.INFO: "Info",
            Severity.WARNING: "Avertissement",
            Severity.RESTORE_NEEDED: "À restaurer",
            Severity.CRITICAL: "Critique",
        },
        "device_kinds": {
            DeviceKind.WHEEL: "Volant",
            DeviceKind.PEDALS: "Pédales",
            DeviceKind.SHIFTER: "Boîte",
            DeviceKind.HANDBRAKE: "Frein à main",
            DeviceKind.BUTTON_BOX: "Boîtier boutons",
            DeviceKind.DDU: "DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Ventilation",
            DeviceKind.OTHER: "Autre",
        },
        "checklist_device_kinds": {
            DeviceKind.WHEEL: "Base volant",
            DeviceKind.PEDALS: "Pédalier",
            DeviceKind.SHIFTER: "Boîte",
            DeviceKind.HANDBRAKE: "Frein à main",
            DeviceKind.BUTTON_BOX: "Boîtier boutons",
            DeviceKind.DDU: "Écran DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Ventilation",
            DeviceKind.OTHER: "Périphérique",
        },
        "software_group": "Logiciels",
        "unknown": "Inconnu",
        "detected_com_status": "{com} détecté",
        "com_mismatch_status": "Attendu {expected}, détecté {detected}",
        "missing_device": "Absent",
        "com_ports": "COM Ports",
        "save": "Sauver",
        "check": "Contrôle",
        "restore": "Restaurer",
        "rollback": "Retour",
        "export": "Exporter",
        "import": "Importer",
        "device_headers": ["Périphérique", "Rôle", "Statut", "USB"],
        "joystick_order": "Ordre Joystick",
        "joystick_headers": ["#", "Joystick", "USB"],
        "usb_health": "USB",
        "tabs": ["Tableau", "Santé USB", "Journaux", "Réglages", "Avancé"],
    },
}


class BackgroundWidget(QWidget):
    def __init__(self, asset_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source = asset_pixmap(asset_name)
        self._scaled = QPixmap()
        self._scaled_size = self.size()
        self.setObjectName("AppBackground")

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        if self._source.isNull():
            painter.fillRect(self.rect(), QColor("#05070b"))
            return
        if self._scaled.isNull() or self._scaled_size != self.size():
            self._scaled = self._source.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_size = self.size()
        x = (self.width() - self._scaled.width()) // 2
        y = (self.height() - self._scaled.height()) // 2
        painter.drawPixmap(x, y, self._scaled)
        event.accept()


class SeparatorTableWidget(QTableWidget):
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().paintEvent(event)
        self._paint_column_separators()

    def _paint_column_separators(self) -> None:
        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor(255, 255, 255, 185), 1))
        header = self.horizontalHeader()
        last_visible = -1
        for visual_index in range(header.count()):
            logical_index = header.logicalIndex(visual_index)
            if not self.isColumnHidden(logical_index):
                last_visible = logical_index
        for visual_index in range(header.count()):
            logical_index = header.logicalIndex(visual_index)
            if logical_index == last_visible or self.isColumnHidden(logical_index):
                continue
            x = header.sectionViewportPosition(logical_index) + header.sectionSize(logical_index) - 1
            if 0 < x < self.viewport().width() - 1:
                painter.drawLine(x, 0, x, self.viewport().height())
        painter.end()


class Worker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn) -> None:
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.fn())
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.settings = self.controller.load_settings()
        self.setWindowTitle("Cockpit Guardian")
        self.setWindowIcon(asset_icon("app_icon_256.png"))
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._threads: list[QThread] = []
        self._workers: dict[QThread, Worker] = {}
        self._busy_operations = 0

        self.background = BackgroundWidget("app_background.png")
        root_layout = QVBoxLayout(self.background)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        root_layout.addWidget(self.tabs)
        self.footer = QFrame()
        self.footer.setObjectName("AppFooter")
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(12, 3, 12, 5)
        footer_layout.setSpacing(6)
        footer_layout.addStretch(1)
        self.footer_prefix_label = QLabel()
        self.footer_prefix_label.setObjectName("FooterText")
        footer_layout.addWidget(self.footer_prefix_label)
        self.footer_youtube_icon = QLabel()
        self.footer_youtube_icon.setObjectName("FooterYoutubeIcon")
        youtube = asset_pixmap("youtube_icon.png")
        if not youtube.isNull():
            self.footer_youtube_icon.setPixmap(
                youtube.scaled(
                    18,
                    12,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        footer_layout.addWidget(self.footer_youtube_icon)
        self.footer_label = QLabel()
        self.footer_label.setObjectName("FooterText")
        self.footer_label.setTextFormat(Qt.TextFormat.RichText)
        self.footer_label.setOpenExternalLinks(True)
        self.footer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        footer_layout.addWidget(self.footer_label)
        self.footer_version_label = QLabel()
        self.footer_version_label.setObjectName("FooterText")
        footer_layout.addWidget(self.footer_version_label)
        footer_layout.addStretch(1)
        root_layout.addWidget(self.footer)
        self.setCentralWidget(self.background)
        self._build_dashboard()
        self._build_usb_health_tab()
        self._build_logs_tab()
        self._build_settings_tab()
        self._build_advanced_tab()
        self._refresh_dashboard_texts()
        self._update_language_buttons()
        QTimer.singleShot(0, self._resize_dashboard_columns)

        self.tray = GuardianTray(self)
        self.tray.open_requested.connect(self.show_and_raise)
        self.tray.check_requested.connect(self.check_now)
        self.tray.restore_requested.connect(self.restore)
        self.tray.exit_requested.connect(QApplication.instance().quit)
        self.tray.show()

        self.apply_theme()
        QTimer.singleShot(250, self.check_now)

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(app_stylesheet(self.settings.theme))

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._resize_dashboard_columns()

    def _resize_dashboard_columns(self) -> None:
        if not hasattr(self, "device_table"):
            return
        self._set_table_column_widths(self.device_table, [0.22, 0.14, 0.30, 0.34])
        self._set_table_column_widths(self.joystick_table, [0.05, 0.35, 0.60])
        if hasattr(self, "usb_table"):
            self._set_table_column_widths(self.usb_table, [0.20, 0.16, 0.26, 0.38])
        if hasattr(self, "priority_table"):
            self._set_table_column_widths(self.priority_table, [0.50, 0.24, 0.26])

    @staticmethod
    def _set_table_column_widths(table: QTableWidget, ratios: list[float]) -> None:
        width = table.viewport().width()
        if width <= 0:
            return
        assigned = 0
        for column, ratio in enumerate(ratios[:-1]):
            column_width = max(32, int(width * ratio))
            table.setColumnWidth(column, column_width)
            assigned += column_width
        table.setColumnWidth(len(ratios) - 1, max(32, width - assigned - 2))

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column in range(table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(30)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

    @staticmethod
    def _set_table_headers(table: QTableWidget, labels: list[str]) -> None:
        for column, label in enumerate(labels):
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            table.setHorizontalHeaderItem(column, item)

    @staticmethod
    def _table_item(value: str) -> QTableWidgetItem:
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _build_dashboard(self) -> None:
        page = QWidget()
        page.setObjectName("DashboardPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        self.dashboard_header = QFrame()
        self.dashboard_header.setObjectName("DashboardHeader")
        header_layout = QHBoxLayout(self.dashboard_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        logo_block = QWidget()
        logo_block.setObjectName("LogoBlock")
        logo_layout = QVBoxLayout(logo_block)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(2)
        self.dashboard_logo = QLabel()
        self.dashboard_logo.setObjectName("DashboardLogo")
        self.dashboard_logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo = asset_pixmap("ui_logo_cg.png")
        if not logo.isNull():
            self.dashboard_logo.setPixmap(
                logo.scaled(
                    124,
                    37,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.dashboard_logo.setFixedHeight(38)
        self.logo_credit_label = QLabel()
        self.logo_credit_label.setObjectName("LogoCredit")
        self.logo_credit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.logo_credit_label.setFixedHeight(12)
        self.status_title = QLabel("CHECK NOT DONE")
        self.status_title.setObjectName("StatusTitle")
        logo_layout.addWidget(self.dashboard_logo)
        logo_layout.addWidget(self.logo_credit_label)
        logo_layout.addSpacing(4)
        logo_layout.addWidget(self.status_title)
        logo_layout.addStretch(1)
        header_layout.addWidget(logo_block, 1, Qt.AlignmentFlag.AlignTop)

        self.summary_content = QWidget()
        self.summary_content.setObjectName("SummaryContent")
        self.summary_content.setMinimumWidth(420)
        self.summary_content.setMaximumWidth(500)
        self.summary_checklist_layout = QGridLayout(self.summary_content)
        self.summary_checklist_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_checklist_layout.setHorizontalSpacing(18)
        self.summary_checklist_layout.setVerticalSpacing(0)
        header_layout.addWidget(self.summary_content, 2, Qt.AlignmentFlag.AlignTop)

        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        language_layout = QHBoxLayout()
        language_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.addStretch(1)
        self.language_eng_button = QPushButton()
        self.language_eng_button.setObjectName("LanguageButton")
        self.language_eng_button.setCheckable(True)
        self.language_eng_button.setIcon(asset_icon("lang_eng.png"))
        self.language_eng_button.setIconSize(QSize(42, 21))
        self.language_eng_button.setFixedSize(50, 28)
        self.language_eng_button.setToolTip("Switch dashboard language to English")
        self.language_eng_button.clicked.connect(lambda: self._set_language("en"))
        self.language_fr_button = QPushButton()
        self.language_fr_button.setObjectName("LanguageButton")
        self.language_fr_button.setCheckable(True)
        self.language_fr_button.setIcon(asset_icon("lang_fr.png"))
        self.language_fr_button.setIconSize(QSize(42, 21))
        self.language_fr_button.setFixedSize(50, 28)
        self.language_fr_button.setToolTip("Basculer le dashboard en francais")
        self.language_fr_button.clicked.connect(lambda: self._set_language("fr"))
        language_layout.addWidget(self.language_eng_button)
        language_layout.addWidget(self.language_fr_button)
        right_layout.addLayout(language_layout)

        action_panel = QWidget()
        action_panel.setObjectName("ActionPanel")
        action_layout = QGridLayout(action_panel)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setHorizontalSpacing(5)
        action_layout.setVerticalSpacing(5)
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("PrimaryButton")
        self.check_button = QPushButton("Check")
        self.restore_button = QPushButton("Restore")
        self.rollback_button = QPushButton("Rollback")
        self.export_config_button = QPushButton("Export")
        self.import_config_button = QPushButton("Import")
        self.save_button.clicked.connect(self.save_configuration)
        self.check_button.clicked.connect(self.check_now)
        self.restore_button.clicked.connect(self.restore)
        self.rollback_button.clicked.connect(self.rollback)
        self.export_config_button.clicked.connect(self.export_config_backup)
        self.import_config_button.clicked.connect(self.import_config_backup)
        self.export_config_button.setToolTip("Choose a cloud-synced folder such as OneDrive, Google Drive, Dropbox, iCloud, or a NAS.")
        self.import_config_button.setToolTip("Import this backup after reinstalling Windows, then run Restore.")
        for index, button in enumerate(
            [
                self.save_button,
                self.check_button,
                self.restore_button,
                self.rollback_button,
                self.export_config_button,
                self.import_config_button,
            ]
        ):
            action_layout.addWidget(button, index // 2, index % 2)
        right_layout.addWidget(action_panel)
        header_layout.addWidget(right_panel, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.dashboard_header)
        self._apply_status_style(GlobalStatus.CHECK_NOT_DONE)

        tables = QVBoxLayout()
        tables.setSpacing(14)

        self.device_table = SeparatorTableWidget(0, 4)
        self._set_table_headers(self.device_table, ["Device", "Role", "Status", "USB"])
        self._configure_table(self.device_table)
        self.device_table.setAlternatingRowColors(True)
        self.com_ports_panel = self._panel("COM Ports", self.device_table)
        self.com_ports_panel_title = self.com_ports_panel.title_label
        tables.addWidget(self.com_ports_panel, 3)

        self.joystick_table = SeparatorTableWidget(0, 3)
        self._set_table_headers(self.joystick_table, ["#", "Joystick Order", "USB"])
        self._configure_table(self.joystick_table)
        self.joystick_panel = self._panel("Joystick Order", self.joystick_table)
        self.joystick_panel_title = self.joystick_panel.title_label
        tables.addWidget(self.joystick_panel, 2)
        layout.addLayout(tables, 1)

        self.tabs.addTab(page, "Dashboard")

    def _build_usb_health_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.usb_score = QLabel("Stability score: 100")
        self.usb_score.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.usb_score)
        self.usb_table = SeparatorTableWidget(0, 4)
        self._set_table_headers(self.usb_table, ["Time", "Severity", "Device", "Event"])
        self._configure_table(self.usb_table)
        self.usb_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.usb_table)
        self.tabs.addTab(page, "USB Health")

    def _build_logs_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        button_layout = QHBoxLayout()
        refresh = QPushButton("Refresh Logs")
        export = QPushButton("Export Logs")
        refresh.clicked.connect(self.refresh_logs)
        export.clicked.connect(self.export_logs)
        button_layout.addWidget(refresh)
        button_layout.addWidget(export)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        self.tabs.addTab(page, "Logs")
        self.refresh_logs()

    def _build_settings_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.profile_input = QLineEdit(self.settings.profile_name)
        self.ffb_threshold = QDoubleSpinBox()
        self.ffb_threshold.setRange(1, 100)
        self.ffb_threshold.setSuffix("%")
        self.ffb_threshold.setValue(self.settings.ffb_clipping_threshold)
        self.notifications = QCheckBox()
        self.notifications.setChecked(self.settings.notifications_enabled)
        self.launch_startup = QCheckBox()
        self.launch_startup.setChecked(self.settings.launch_at_startup)
        self.auto_restore = QCheckBox()
        self.auto_restore.setChecked(self.settings.auto_restore)
        self.simhub_required = QCheckBox()
        self.simhub_required.setChecked(self.settings.simhub_required)
        self.deep_windows_scan = QCheckBox()
        self.deep_windows_scan.setChecked(self.settings.deep_windows_scan)
        self.software_scan_interval = QSpinBox()
        self.software_scan_interval.setRange(0, 3600)
        self.software_scan_interval.setSuffix(" s")
        self.software_scan_interval.setValue(self.settings.software_scan_interval_seconds)
        self.usb_health_scan_interval = QSpinBox()
        self.usb_health_scan_interval.setRange(0, 3600)
        self.usb_health_scan_interval.setSuffix(" s")
        self.usb_health_scan_interval.setValue(self.settings.usb_health_scan_interval_seconds)
        self.theme_select = QComboBox()
        self.theme_select.addItems(["dark", "light"])
        self.theme_select.setCurrentText(self.settings.theme)
        self.language_select = QComboBox()
        self.language_select.addItems(["en", "fr"])
        self.language_select.setCurrentText(self.settings.language)
        form.addRow("Active profile", self.profile_input)
        form.addRow("FFB clipping threshold", self.ffb_threshold)
        form.addRow("Notifications", self.notifications)
        form.addRow("Launch at Windows startup", self.launch_startup)
        form.addRow("Auto-restore", self.auto_restore)
        form.addRow("SimHub is required", self.simhub_required)
        form.addRow("Deep Windows scan", self.deep_windows_scan)
        form.addRow("Software scan cache", self.software_scan_interval)
        form.addRow("USB Health cache", self.usb_health_scan_interval)
        form.addRow("Theme", self.theme_select)
        form.addRow("Language", self.language_select)
        layout.addLayout(form)

        save = QPushButton("Save Settings")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.save_settings)
        layout.addWidget(save)

        priority_label = QLabel("Device priority")
        priority_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(priority_label)
        self.priority_table = SeparatorTableWidget(0, 3)
        self._set_table_headers(self.priority_table, ["Device", "Role", "Priority"])
        self._configure_table(self.priority_table)
        self.priority_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.priority_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.priority_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.priority_table)
        self._load_priority_table()
        layout.addStretch(1)
        self.tabs.addTab(page, "Settings")

    def _build_advanced_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        refresh = QPushButton("Refresh Debug Data")
        refresh.clicked.connect(self.refresh_advanced)
        layout.addWidget(refresh)
        self.advanced_tree = QTreeWidget()
        self.advanced_tree.setHeaderLabels(["Field", "Value"])
        self.advanced_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.advanced_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.advanced_tree)
        self.tabs.addTab(page, "Advanced / Debug")
        self.refresh_advanced()

    def _panel(self, title: str, child: QWidget) -> QWidget:
        panel = QFrame()
        panel.setObjectName("DataPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)
        label = QLabel(title)
        label.setObjectName("PanelTitle")
        label.setStyleSheet("font-size: 12px; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(child)
        panel.title_label = label
        return panel

    def _run_async(self, fn, callback) -> None:
        self._set_busy(True)
        thread = QThread(self)
        worker = Worker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(callback)
        worker.failed.connect(self._operation_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._finish_thread(thread))
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        self._workers[thread] = worker
        self._busy_operations += 1
        thread.start()

    def _finish_thread(self, thread: QThread) -> None:
        self._busy_operations = max(0, self._busy_operations - 1)
        self._set_busy(self._busy_operations > 0)
        if thread in self._threads:
            self._threads.remove(thread)
        self._workers.pop(thread, None)

    def _set_busy(self, busy: bool) -> None:
        for button in [
            self.save_button,
            self.check_button,
            self.restore_button,
            self.rollback_button,
            self.export_config_button,
            self.import_config_button,
        ]:
            button.setDisabled(busy)

    def save_configuration(self) -> None:
        self._run_async(self.controller.save_configuration, self._save_configuration_finished)

    def _save_configuration_finished(self, _) -> None:
        self.check_now()

    def check_now(self) -> None:
        self._run_async(self.controller.check_now, self.update_report)

    def restore(self) -> None:
        self._run_async(self.controller.restore, self._restore_finished)

    def rollback(self) -> None:
        self._run_async(self.controller.rollback_last_restore, self._rollback_finished)

    def export_config_backup(self) -> None:
        default_path = Path.home() / self.controller.default_config_backup_name()
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Export Config Backup",
            str(default_path),
            "Cockpit Guardian backup (*.json);;JSON files (*.json)",
        )
        if not target:
            return
        self._run_async(lambda: self.controller.export_config_backup(Path(target)), self._export_config_finished)

    def import_config_backup(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Import Config Backup",
            str(Path.home()),
            "Cockpit Guardian backup (*.json);;JSON files (*.json)",
        )
        if not source:
            return
        answer = QMessageBox.question(
            self,
            "Import Config Backup",
            "Importing will replace the current saved configuration after creating a local safety backup. Continue?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run_async(lambda: self.controller.import_config_backup(Path(source)), self._import_config_finished)

    def _restore_finished(self, report: RestoreReport) -> None:
        QMessageBox.information(self, "Restore", "\n".join(action.message for action in report.actions))
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _rollback_finished(self, action) -> None:
        QMessageBox.information(self, "Rollback Last Restore", action.message)
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _export_config_finished(self, path: Path) -> None:
        QMessageBox.information(
            self,
            "Export Config Backup",
            f"Configuration backup exported to:\n{path}\n\nStore this file in a cloud-synced folder before reinstalling Windows.",
        )

    def _import_config_finished(self, backup_path: Path) -> None:
        QMessageBox.information(
            self,
            "Import Config Backup",
            f"Configuration imported. A local safety backup was created at:\n{backup_path}\n\nRun Restore if the check reports changed COM ports or joystick order.",
        )
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _operation_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Cockpit Guardian", message)

    def update_report(self, report: CheckReport) -> None:
        self.status_title.setText(self._status_text(report.global_status).upper())
        self._apply_status_style(report.global_status)
        self.tray.update_report(report)
        self._update_device_table(report)
        self._update_joystick(report)
        self._update_summary(report)
        self._update_usb(report)
        self._load_priority_table()
        self.refresh_logs()
        self.refresh_advanced()

    def _apply_status_style(self, status: GlobalStatus) -> None:
        color = STATUS_COLORS.get(status, "#6b7280")
        self.status_title.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {color}; background: transparent;"
        )

    def _dashboard_text(self, key: str):
        language = self.settings.language if self.settings.language in DASHBOARD_TEXT else "en"
        return DASHBOARD_TEXT[language][key]

    def _status_text(self, status: GlobalStatus) -> str:
        return self._dashboard_text("status_labels").get(status, status.value)

    def _severity_text(self, severity: Severity) -> str:
        return self._dashboard_text("severity_labels").get(severity, severity.value)

    def _device_kind_text(self, kind: DeviceKind | None) -> str:
        if not kind:
            return self._dashboard_text("unknown")
        return self._dashboard_text("device_kinds").get(kind, kind.value)

    def _checklist_device_kind_text(self, kind: DeviceKind | None) -> str:
        if not kind:
            return self._dashboard_text("unknown")
        return self._dashboard_text("checklist_device_kinds").get(kind, self._device_kind_text(kind))

    def _refresh_dashboard_texts(self) -> None:
        status = self.controller.last_report.global_status if self.controller.last_report else GlobalStatus.CHECK_NOT_DONE
        self.status_title.setText(self._status_text(status).upper())
        self.save_button.setText(self._dashboard_text("save"))
        self.check_button.setText(self._dashboard_text("check"))
        self.restore_button.setText(self._dashboard_text("restore"))
        self.rollback_button.setText(self._dashboard_text("rollback"))
        self.export_config_button.setText(self._dashboard_text("export"))
        self.import_config_button.setText(self._dashboard_text("import"))
        self.logo_credit_label.setText(self._dashboard_text("logo_credit"))
        self.com_ports_panel_title.setText(self._dashboard_text("com_ports"))
        self._set_table_headers(self.device_table, self._dashboard_text("device_headers"))
        self._set_table_headers(self.joystick_table, self._dashboard_text("joystick_headers"))
        self.joystick_panel_title.setText(self._dashboard_text("joystick_order"))
        tabs = self._dashboard_text("tabs")
        for index, label in enumerate(tabs):
            if index < self.tabs.count():
                self.tabs.setTabText(index, label)
        if self.controller.last_report:
            report = self.controller.last_report
            self._update_summary(report)
        else:
            self._clear_layout(self.summary_checklist_layout)
        self.footer_prefix_label.setText(self._dashboard_text("footer_prefix"))
        self.footer_label.setText(
            f'<a style="color: #ffffff; text-decoration: none;" href="{YOUTUBE_URL}">REALISTIC SIMCOCKPIT</a>'
        )
        self.footer_version_label.setText(f'| {self._dashboard_text("footer_version")} {__version__}')

    def _set_language(self, language: str) -> None:
        if language not in DASHBOARD_TEXT:
            return
        self.settings.language = language
        if hasattr(self, "language_select"):
            self.language_select.setCurrentText(language)
        self.controller.save_settings(self.settings)
        self._refresh_dashboard_texts()
        if self.controller.last_report:
            self.update_report(self.controller.last_report)
        self._update_language_buttons()

    def _update_language_buttons(self) -> None:
        language = self.settings.language if self.settings.language in DASHBOARD_TEXT else "en"
        self.language_eng_button.setChecked(language == "en")
        self.language_fr_button.setChecked(language == "fr")

    def _update_device_table(self, report: CheckReport) -> None:
        self.device_table.setRowCount(0)
        for check in report.device_checks:
            if not self._is_serial_check(check):
                continue
            device = check.expected or check.detected
            usb_device = check.detected or check.expected
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            role = self._device_kind_text(device.kind if device else None)
            usb = self._usb_summary(usb_device)
            detail = check.detail or ""
            if check.ffb_clipping_percent is not None:
                detail = f"FFB clipping {check.ffb_clipping_percent:.0f}% - Reduce in-game FFB gain"
            tooltip = detail or check.message
            values = [check.label, role, self._device_status_text(check), usb]
            for column, value in enumerate(values):
                item = self._table_item(value)
                item.setToolTip(tooltip)
                if column == 2:
                    item.setForeground(QColor(SEVERITY_COLORS.get(check.severity, "#e5e7eb")))
                self.device_table.setItem(row, column, item)

    @staticmethod
    def _is_serial_check(check: DeviceCheck) -> bool:
        return any(device.bus == DeviceBus.SERIAL or device.serial for device in (check.expected, check.detected) if device)

    def _device_status_text(self, check: DeviceCheck) -> str:
        if check.severity == Severity.OK:
            return self._severity_text(check.severity)
        expected_com = check.expected.serial.current_com if check.expected and check.expected.serial else None
        detected_com = check.detected.serial.current_com if check.detected and check.detected.serial else None
        if check.severity == Severity.RESTORE_NEEDED and expected_com and detected_com and expected_com != detected_com:
            return self._dashboard_text("com_mismatch_status").format(expected=expected_com, detected=detected_com)
        if check.detected is None:
            if expected_com:
                return self._dashboard_text("missing_device") + f" - {expected_com}"
            return self._dashboard_text("missing_device")
        if detected_com:
            return self._dashboard_text("detected_com_status").format(com=detected_com)
        return self._severity_text(check.severity)

    def _usb_summary(self, device) -> str:
        if not device or not device.usb:
            return self._dashboard_text("unknown")
        if device.usb.negotiated_speed_mbps:
            return f"{device.usb.label} ({device.usb.negotiated_speed_mbps} Mbps)"
        if device.usb.confidence and device.usb.confidence != "unknown":
            return f"{device.usb.label} ({device.usb.confidence})"
        return device.usb.label

    def _update_joystick(self, report: CheckReport) -> None:
        order = report.joystick_order.current or report.joystick_order.expected
        devices_by_name = self._devices_by_joystick_name(report)
        self.joystick_table.setRowCount(0)
        for index, name in enumerate(order, start=1):
            row = self.joystick_table.rowCount()
            self.joystick_table.insertRow(row)
            device = devices_by_name.get(name.lower())
            self.joystick_table.setItem(row, 0, self._table_item(str(index)))
            self.joystick_table.setItem(row, 1, self._table_item(name))
            self.joystick_table.setItem(row, 2, self._table_item(self._usb_summary(device)))
        if not order:
            self.joystick_table.insertRow(0)
            self.joystick_table.setItem(0, 0, self._table_item("-"))
            self.joystick_table.setItem(0, 1, self._table_item(report.joystick_order.message))
            self.joystick_table.setItem(0, 2, self._table_item("-"))

    @staticmethod
    def _devices_by_joystick_name(report: CheckReport) -> dict[str, object]:
        devices: dict[str, object] = {}
        for check in report.device_checks:
            device = check.detected or check.expected
            if not device:
                continue
            names = {device.label, device.display_name}
            if device.hid and device.hid.name:
                names.add(device.hid.name)
            for name in names:
                if name:
                    devices[name.lower()] = device
        return devices

    def _update_summary(self, report: CheckReport) -> None:
        self._clear_layout(self.summary_checklist_layout)
        items = [
            (self._dashboard_text("usb_health"), report.usb_health.severity),
            (self._dashboard_text("joystick_order"), Severity.OK if report.joystick_order.ok else Severity.WARNING),
        ]
        seen_device_ids: set[str] = set()
        for check in report.device_checks:
            device = check.expected or check.detected
            if not device or device.id in seen_device_ids:
                continue
            seen_device_ids.add(device.id)
            items.append((self._checklist_device_kind_text(device.kind), check.severity))
        if report.software:
            items.append((self._dashboard_text("software_group"), self._software_summary_severity(report.software)))
        for index, (label, severity) in enumerate(items):
            self._add_checklist_row(self.summary_checklist_layout, index, label, severity)

    def _add_checklist_row(self, layout: QGridLayout, index: int, label: str, severity: Severity) -> None:
        row = QWidget()
        row.setObjectName("ChecklistRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(3)
        label_widget = QLabel(label)
        label_widget.setObjectName("ChecklistName")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_widget.setWordWrap(False)
        icon_widget = QLabel(self._status_icon(severity))
        icon_widget.setObjectName("ChecklistIcon")
        icon_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        icon_widget.setFixedWidth(13)
        icon_widget.setStyleSheet(f"color: {SEVERITY_COLORS.get(severity, '#e5e7eb')};")
        row_layout.addWidget(label_widget, 1)
        row_layout.addWidget(icon_widget)
        column = min(index // CHECKLIST_ROWS_PER_COLUMN, CHECKLIST_COLUMNS - 1)
        grid_row = index % CHECKLIST_ROWS_PER_COLUMN
        if index >= CHECKLIST_ROWS_PER_COLUMN * CHECKLIST_COLUMNS:
            grid_row = CHECKLIST_ROWS_PER_COLUMN + index - (CHECKLIST_ROWS_PER_COLUMN * CHECKLIST_COLUMNS)
        layout.addWidget(row, grid_row, column)

    @staticmethod
    def _status_icon(severity: Severity) -> str:
        if severity == Severity.OK:
            return "✓"
        if severity in {Severity.WARNING, Severity.RESTORE_NEEDED, Severity.INFO}:
            return "⚠"
        return "✕"

    @staticmethod
    def _severity_from_software_state(state: SoftwareState) -> Severity:
        if state == SoftwareState.RUNNING:
            return Severity.OK
        if state == SoftwareState.INSTALLED_CLOSED:
            return Severity.WARNING
        if state == SoftwareState.REQUIRED_MISSING:
            return Severity.CRITICAL
        return Severity.INFO

    @classmethod
    def _software_summary_severity(cls, software: list) -> Severity:
        rank = {
            Severity.OK: 0,
            Severity.INFO: 1,
            Severity.WARNING: 2,
            Severity.RESTORE_NEEDED: 3,
            Severity.CRITICAL: 4,
        }
        severity = Severity.OK
        for item in software:
            item_severity = cls._severity_from_software_state(item.state)
            if rank[item_severity] > rank[severity]:
                severity = item_severity
        return severity

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _update_usb(self, report: CheckReport) -> None:
        self.usb_score.setText(f"Stability score: {report.usb_health.stability_score}")
        self.usb_table.setRowCount(0)
        for event in report.usb_health.events:
            row = self.usb_table.rowCount()
            self.usb_table.insertRow(row)
            for column, value in enumerate([event.timestamp, event.severity.value, event.device_name, event.message]):
                self.usb_table.setItem(row, column, self._table_item(value))

    def save_settings(self) -> None:
        self.settings = Settings(
            profile_name=self.profile_input.text().strip() or "Default Cockpit",
            ffb_clipping_threshold=float(self.ffb_threshold.value()),
            notifications_enabled=self.notifications.isChecked(),
            launch_at_startup=self.launch_startup.isChecked(),
            auto_restore=self.auto_restore.isChecked(),
            theme=self.theme_select.currentText(),
            language=self.language_select.currentText(),
            simhub_required=self.simhub_required.isChecked(),
            deep_windows_scan=self.deep_windows_scan.isChecked(),
            initial_deep_windows_scan_done=self.settings.initial_deep_windows_scan_done,
            software_scan_interval_seconds=int(self.software_scan_interval.value()),
            usb_health_scan_interval_seconds=int(self.usb_health_scan_interval.value()),
        )
        self.controller.save_settings(self.settings)
        self._save_device_priorities()
        self.apply_theme()
        self._refresh_dashboard_texts()
        self._update_language_buttons()
        QMessageBox.information(self, "Settings", "Settings saved.")

    def _load_priority_table(self) -> None:
        if not hasattr(self, "priority_table"):
            return
        self.priority_table.setRowCount(0)
        snapshot = self.controller.load_snapshot()
        if not snapshot:
            self.priority_table.insertRow(0)
            self.priority_table.setItem(0, 0, QTableWidgetItem("No saved configuration yet"))
            self.priority_table.setItem(0, 1, QTableWidgetItem("-"))
            self.priority_table.setItem(0, 2, QTableWidgetItem("-"))
            return
        for device in snapshot.devices:
            row = self.priority_table.rowCount()
            self.priority_table.insertRow(row)
            id_item = QTableWidgetItem(device.label)
            id_item.setData(Qt.ItemDataRole.UserRole, device.id)
            self.priority_table.setItem(row, 0, id_item)
            self.priority_table.setItem(row, 1, QTableWidgetItem(device.kind.value.replace("_", " ").title()))
            combo = QComboBox()
            combo.addItems([Priority.REQUIRED.value, Priority.OPTIONAL.value, Priority.IGNORED.value])
            combo.setCurrentText(device.priority.value)
            self.priority_table.setCellWidget(row, 2, combo)

    def _save_device_priorities(self) -> None:
        snapshot = self.controller.load_snapshot()
        if not snapshot:
            return
        priority_by_id: dict[str, Priority] = {}
        for row in range(self.priority_table.rowCount()):
            id_item = self.priority_table.item(row, 0)
            combo = self.priority_table.cellWidget(row, 2)
            if not id_item or not isinstance(combo, QComboBox):
                continue
            device_id = id_item.data(Qt.ItemDataRole.UserRole)
            if device_id:
                priority_by_id[str(device_id)] = Priority(combo.currentText())
        if not priority_by_id:
            return
        for device in snapshot.devices:
            if device.id in priority_by_id:
                device.priority = priority_by_id[device.id]
        self.controller.config.save_snapshot(snapshot)

    def refresh_logs(self) -> None:
        path = self.controller.config.paths.log_file
        if path.exists():
            self.logs_text.setPlainText(path.read_text(encoding="utf-8")[-12000:])
        else:
            self.logs_text.setPlainText("")

    def export_logs(self) -> None:
        default_path = self.controller.config.paths.exports / "cockpit_guardian.log"
        target, _ = QFileDialog.getSaveFileName(self, "Export Logs", str(default_path), "Log files (*.log);;Text files (*.txt)")
        if target:
            self.controller.config.export_logs(Path(target))
            QMessageBox.information(self, "Export Logs", f"Logs exported to {target}.")

    def refresh_advanced(self) -> None:
        self.advanced_tree.clear()
        snapshot = self.controller.load_snapshot()
        root = QTreeWidgetItem(["Data directory", str(self.controller.config.paths.root)])
        self.advanced_tree.addTopLevelItem(root)
        notices = QTreeWidgetItem(["Integration notices", "SimHub, Arduino, ESP, Windows"])
        for notice in INTEGRATION_NOTICES:
            notices.addChild(QTreeWidgetItem([notice.title, notice.body]))
        self.advanced_tree.addTopLevelItem(notices)
        if snapshot:
            snap = QTreeWidgetItem(["Snapshot", snapshot.snapshot_date])
            snap.addChild(QTreeWidgetItem(["Profile", snapshot.profile_name]))
            snap.addChild(QTreeWidgetItem(["App version", snapshot.app_version]))
            for device in snapshot.devices:
                node = QTreeWidgetItem([device.label, device.bus.value])
                node.addChild(QTreeWidgetItem(["Priority", device.priority.value]))
                node.addChild(QTreeWidgetItem(["Kind", device.kind.value]))
                if device.serial:
                    serial = QTreeWidgetItem(["Serial / COM", device.serial.current_com or ""])
                    for key, value in to_plain(device.serial).items():
                        serial.addChild(QTreeWidgetItem([key, str(value)]))
                    node.addChild(serial)
                if device.hid:
                    hid = QTreeWidgetItem(["HID / DirectInput", device.hid.name or ""])
                    for key, value in to_plain(device.hid).items():
                        hid.addChild(QTreeWidgetItem([key, str(value)]))
                    node.addChild(hid)
                if device.usb:
                    usb = QTreeWidgetItem(["USB", device.usb.label])
                    for key, value in to_plain(device.usb).items():
                        usb.addChild(QTreeWidgetItem([key, str(value)]))
                    node.addChild(usb)
                snap.addChild(node)
            self.advanced_tree.addTopLevelItem(snap)
        else:
            self.advanced_tree.addTopLevelItem(QTreeWidgetItem(["Snapshot", "Not saved yet"]))
        self.advanced_tree.expandToDepth(1)

    def show_and_raise(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
