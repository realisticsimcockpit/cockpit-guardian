from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
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

from ..controller import AppController
from ..models import CheckReport, GlobalStatus, Priority, RestoreReport, Settings, to_plain
from .assets import asset_icon, asset_pixmap
from .theme import SEVERITY_COLORS, STATUS_COLORS, app_stylesheet
from .tray import GuardianTray
from ..services.integration_notices import INTEGRATION_NOTICES


WINDOW_WIDTH = 724
WINDOW_HEIGHT = 543

DASHBOARD_TEXT = {
    "en": {
        "status_initial": "Save config, then run a check.",
        "status_ready": "All saved cockpit devices look ready.",
        "save": "Save",
        "check": "Check",
        "restore": "Restore",
        "rollback": "Rollback",
        "export": "Export",
        "import": "Import",
        "device_headers": ["Device", "Role", "Status", "USB"],
        "joystick_order": "Joystick Order",
        "usb_software": "USB Health and Software",
        "area": "Area",
        "status": "Status",
        "tabs": ["Dashboard", "USB Health", "Logs", "Settings", "Advanced"],
    },
    "fr": {
        "status_initial": "Sauvegardez, puis controlez.",
        "status_ready": "Les peripheriques sauvegardes sont prets.",
        "save": "Sauver",
        "check": "Controle",
        "restore": "Restaurer",
        "rollback": "Retour",
        "export": "Exporter",
        "import": "Importer",
        "device_headers": ["Peripherique", "Role", "Statut", "USB"],
        "joystick_order": "Ordre Joystick",
        "usb_software": "USB et logiciels",
        "area": "Zone",
        "status": "Statut",
        "tabs": ["Dashboard", "USB Health", "Logs", "Settings", "Avance"],
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
        self.setCentralWidget(self.background)
        self._build_dashboard()
        self._build_usb_health_tab()
        self._build_logs_tab()
        self._build_settings_tab()
        self._build_advanced_tab()
        self._refresh_dashboard_texts()
        self._update_language_buttons()

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

    def _build_dashboard(self) -> None:
        page = QWidget()
        page.setObjectName("DashboardPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(9, 8, 9, 9)
        layout.setSpacing(7)

        self.dashboard_header = QFrame()
        self.dashboard_header.setObjectName("DashboardHeader")
        header_layout = QHBoxLayout(self.dashboard_header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        status_block = QWidget()
        status_block.setObjectName("StatusBlock")
        status_layout = QVBoxLayout(status_block)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        self.status_title = QLabel("CHECK NOT DONE")
        self.status_title.setObjectName("StatusTitle")
        self.status_subtitle = QLabel("Save your cockpit configuration, then run a check.")
        self.status_subtitle.setObjectName("StatusSubtitle")
        self.status_subtitle.setWordWrap(True)
        status_layout.addWidget(self.status_title)
        status_layout.addWidget(self.status_subtitle)
        status_layout.addStretch(1)
        header_layout.addWidget(status_block, 2)

        self.dashboard_logo = QLabel()
        self.dashboard_logo.setObjectName("DashboardLogo")
        self.dashboard_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = asset_pixmap("ui_logo_cg.png")
        if not logo.isNull():
            self.dashboard_logo.setPixmap(
                logo.scaled(
                    210,
                    63,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.dashboard_logo.setMaximumHeight(66)
        header_layout.addWidget(self.dashboard_logo, 3)

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
        self.language_eng_button.setIconSize(QSize(36, 18))
        self.language_eng_button.setFixedSize(44, 24)
        self.language_eng_button.setToolTip("Switch dashboard language to English")
        self.language_eng_button.clicked.connect(lambda: self._set_language("en"))
        self.language_fr_button = QPushButton()
        self.language_fr_button.setObjectName("LanguageButton")
        self.language_fr_button.setCheckable(True)
        self.language_fr_button.setIcon(asset_icon("lang_fr.png"))
        self.language_fr_button.setIconSize(QSize(36, 18))
        self.language_fr_button.setFixedSize(44, 24)
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
        header_layout.addWidget(right_panel, 2)
        layout.addWidget(self.dashboard_header)
        self._apply_status_style(GlobalStatus.CHECK_NOT_DONE)

        self.device_table = QTableWidget(0, 4)
        self.device_table.setHorizontalHeaderLabels(["Device", "Role", "Status", "USB"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.setAlternatingRowColors(True)
        self.device_table.setShowGrid(True)
        self.device_table.setGridStyle(Qt.PenStyle.SolidLine)
        layout.addWidget(self.device_table, 2)

        bottom = QHBoxLayout()
        self.joystick_table = QTableWidget(0, 2)
        self.joystick_table.setHorizontalHeaderLabels(["#", "Joystick Order"])
        self.joystick_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.joystick_table.verticalHeader().setVisible(False)
        self.joystick_table.setShowGrid(True)
        self.joystick_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.joystick_panel = self._panel("Joystick Order", self.joystick_table)
        self.joystick_panel_title = self.joystick_panel.title_label
        bottom.addWidget(self.joystick_panel, 2)

        self.summary_tree = QTreeWidget()
        self.summary_tree.setHeaderLabels(["Area", "Status"])
        self.summary_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.summary_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.summary_panel = self._panel("USB Health and Software", self.summary_tree)
        self.summary_panel_title = self.summary_panel.title_label
        bottom.addWidget(self.summary_panel, 3)
        layout.addLayout(bottom, 2)

        self.tabs.addTab(page, "Dashboard")

    def _build_usb_health_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.usb_score = QLabel("Stability score: 100")
        self.usb_score.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.usb_score)
        self.usb_table = QTableWidget(0, 4)
        self.usb_table.setHorizontalHeaderLabels(["Time", "Severity", "Device", "Event"])
        self.usb_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.usb_table.verticalHeader().setVisible(False)
        self.usb_table.setShowGrid(True)
        self.usb_table.setGridStyle(Qt.PenStyle.SolidLine)
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
        self.priority_table = QTableWidget(0, 3)
        self.priority_table.setHorizontalHeaderLabels(["Device", "Role", "Priority"])
        self.priority_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.priority_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.priority_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.priority_table.verticalHeader().setVisible(False)
        self.priority_table.setShowGrid(True)
        self.priority_table.setGridStyle(Qt.PenStyle.SolidLine)
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
        panel = QWidget()
        layout = QVBoxLayout(panel)
        label = QLabel(title)
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
        self.status_title.setText(report.global_status.value.upper())
        self.status_subtitle.setText(report.issues[0] if report.issues else self._dashboard_text("status_ready"))
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
        self.status_subtitle.setStyleSheet("font-size: 10px; color: #d1d5db; background: transparent;")

    def _dashboard_text(self, key: str):
        language = self.settings.language if self.settings.language in DASHBOARD_TEXT else "en"
        return DASHBOARD_TEXT[language][key]

    def _refresh_dashboard_texts(self) -> None:
        self.status_subtitle.setText(self._dashboard_text("status_initial"))
        self.save_button.setText(self._dashboard_text("save"))
        self.check_button.setText(self._dashboard_text("check"))
        self.restore_button.setText(self._dashboard_text("restore"))
        self.rollback_button.setText(self._dashboard_text("rollback"))
        self.export_config_button.setText(self._dashboard_text("export"))
        self.import_config_button.setText(self._dashboard_text("import"))
        self.device_table.setHorizontalHeaderLabels(self._dashboard_text("device_headers"))
        self.joystick_table.setHorizontalHeaderLabels(["#", self._dashboard_text("joystick_order")])
        self.summary_tree.setHeaderLabels([self._dashboard_text("area"), self._dashboard_text("status")])
        self.joystick_panel_title.setText(self._dashboard_text("joystick_order"))
        self.summary_panel_title.setText(self._dashboard_text("usb_software"))
        tabs = self._dashboard_text("tabs")
        for index, label in enumerate(tabs):
            if index < self.tabs.count():
                self.tabs.setTabText(index, label)
        if self.controller.last_report:
            report = self.controller.last_report
            self.status_subtitle.setText(report.issues[0] if report.issues else self._dashboard_text("status_ready"))

    def _set_language(self, language: str) -> None:
        if language not in DASHBOARD_TEXT:
            return
        self.settings.language = language
        if hasattr(self, "language_select"):
            self.language_select.setCurrentText(language)
        self.controller.save_settings(self.settings)
        self._refresh_dashboard_texts()
        self._update_language_buttons()

    def _update_language_buttons(self) -> None:
        language = self.settings.language if self.settings.language in DASHBOARD_TEXT else "en"
        self.language_eng_button.setChecked(language == "en")
        self.language_fr_button.setChecked(language == "fr")

    def _update_device_table(self, report: CheckReport) -> None:
        self.device_table.setRowCount(0)
        for check in report.device_checks:
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            device = check.expected or check.detected
            role = device.kind.value.replace("_", " ").title() if device else "Unknown"
            usb = self._usb_summary(device)
            detail = check.detail or ""
            if check.ffb_clipping_percent is not None:
                detail = f"FFB clipping {check.ffb_clipping_percent:.0f}% - Reduce in-game FFB gain"
            tooltip = detail or check.message
            values = [check.label, role, check.severity.value.replace("_", " ").title(), usb]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(tooltip)
                if column == 2:
                    item.setForeground(QColor(SEVERITY_COLORS.get(check.severity, "#e5e7eb")))
                self.device_table.setItem(row, column, item)

    @staticmethod
    def _usb_summary(device) -> str:
        if not device or not device.usb:
            return "Unknown"
        if device.usb.negotiated_speed_mbps:
            return f"{device.usb.label} ({device.usb.negotiated_speed_mbps} Mbps)"
        if device.usb.confidence and device.usb.confidence != "unknown":
            return f"{device.usb.label} ({device.usb.confidence})"
        return device.usb.label

    def _update_joystick(self, report: CheckReport) -> None:
        order = report.joystick_order.current or report.joystick_order.expected
        self.joystick_table.setRowCount(0)
        for index, name in enumerate(order, start=1):
            row = self.joystick_table.rowCount()
            self.joystick_table.insertRow(row)
            self.joystick_table.setItem(row, 0, QTableWidgetItem(str(index)))
            self.joystick_table.setItem(row, 1, QTableWidgetItem(name))
        if not order:
            self.joystick_table.insertRow(0)
            self.joystick_table.setItem(0, 0, QTableWidgetItem("-"))
            self.joystick_table.setItem(0, 1, QTableWidgetItem(report.joystick_order.message))

    def _update_summary(self, report: CheckReport) -> None:
        self.summary_tree.clear()
        self.summary_tree.addTopLevelItem(QTreeWidgetItem(["USB Health", report.usb_health.message]))
        self.summary_tree.addTopLevelItem(QTreeWidgetItem(["Joystick Order", report.joystick_order.message]))
        for software in report.software:
            self.summary_tree.addTopLevelItem(QTreeWidgetItem([software.name, software.state.value]))
        self.summary_tree.expandAll()

    def _update_usb(self, report: CheckReport) -> None:
        self.usb_score.setText(f"Stability score: {report.usb_health.stability_score}")
        self.usb_table.setRowCount(0)
        for event in report.usb_health.events:
            row = self.usb_table.rowCount()
            self.usb_table.insertRow(row)
            for column, value in enumerate([event.timestamp, event.severity.value, event.device_name, event.message]):
                self.usb_table.setItem(row, column, QTableWidgetItem(value))

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
