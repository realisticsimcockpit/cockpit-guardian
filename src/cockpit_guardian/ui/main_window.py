from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
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
from .theme import SEVERITY_COLORS, STATUS_COLORS, app_stylesheet
from .tray import GuardianTray
from ..services.integration_notices import INTEGRATION_NOTICES


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
        self.resize(1180, 760)
        self._threads: list[QThread] = []
        self._workers: dict[QThread, Worker] = {}
        self._busy_operations = 0

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_dashboard()
        self._build_usb_health_tab()
        self._build_logs_tab()
        self._build_settings_tab()
        self._build_advanced_tab()

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
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.status_banner = QFrame()
        self.status_banner.setObjectName("StatusBanner")
        banner_layout = QVBoxLayout(self.status_banner)
        self.status_title = QLabel("CHECK NOT DONE")
        self.status_title.setStyleSheet("font-size: 30px; font-weight: 800; background: transparent;")
        self.status_subtitle = QLabel("Save your cockpit configuration, then run a check.")
        self.status_subtitle.setStyleSheet("background: transparent;")
        banner_layout.addWidget(self.status_title)
        banner_layout.addWidget(self.status_subtitle)
        layout.addWidget(self.status_banner)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Configuration")
        self.save_button.setObjectName("PrimaryButton")
        self.check_button = QPushButton("Check Now")
        self.restore_button = QPushButton("Restore")
        self.rollback_button = QPushButton("Rollback Last Restore")
        self.save_button.clicked.connect(self.save_configuration)
        self.check_button.clicked.connect(self.check_now)
        self.restore_button.clicked.connect(self.restore)
        self.rollback_button.clicked.connect(self.rollback)
        for button in [self.save_button, self.check_button, self.restore_button, self.rollback_button]:
            button_layout.addWidget(button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        self.device_table = QTableWidget(0, 4)
        self.device_table.setHorizontalHeaderLabels(["Device", "Role", "Status", "Detail"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.setAlternatingRowColors(True)
        layout.addWidget(self.device_table, 3)

        bottom = QHBoxLayout()
        self.joystick_table = QTableWidget(0, 2)
        self.joystick_table.setHorizontalHeaderLabels(["#", "Joystick Order"])
        self.joystick_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.joystick_table.verticalHeader().setVisible(False)
        bottom.addWidget(self._panel("Joystick Order", self.joystick_table), 2)

        self.summary_tree = QTreeWidget()
        self.summary_tree.setHeaderLabels(["Area", "Status"])
        self.summary_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.summary_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        bottom.addWidget(self._panel("USB Health and Software", self.summary_tree), 3)
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

    @staticmethod
    def _panel(title: str, child: QWidget) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        label = QLabel(title)
        label.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(child)
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
        for button in [self.save_button, self.check_button, self.restore_button, self.rollback_button]:
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

    def _restore_finished(self, report: RestoreReport) -> None:
        QMessageBox.information(self, "Restore", "\n".join(action.message for action in report.actions))
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _rollback_finished(self, action) -> None:
        QMessageBox.information(self, "Rollback Last Restore", action.message)
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _operation_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Cockpit Guardian", message)

    def update_report(self, report: CheckReport) -> None:
        self.status_title.setText(report.global_status.value.upper())
        self.status_subtitle.setText(report.issues[0] if report.issues else "All saved cockpit devices look ready.")
        self.status_banner.setStyleSheet(f"QFrame#StatusBanner {{ background: {STATUS_COLORS.get(report.global_status, '#6b7280')}; }}")
        self.tray.update_report(report)
        self._update_device_table(report)
        self._update_joystick(report)
        self._update_summary(report)
        self._update_usb(report)
        self._load_priority_table()
        self.refresh_logs()
        self.refresh_advanced()

    def _update_device_table(self, report: CheckReport) -> None:
        self.device_table.setRowCount(0)
        for check in report.device_checks:
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            device = check.expected or check.detected
            role = device.kind.value.replace("_", " ").title() if device else "Unknown"
            detail = check.detail or ""
            if check.ffb_clipping_percent is not None:
                detail = f"FFB clipping {check.ffb_clipping_percent:.0f}% - Reduce in-game FFB gain"
            values = [check.label, role, check.severity.value.replace("_", " ").title(), detail or check.message]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 2:
                    item.setForeground(QColor(SEVERITY_COLORS.get(check.severity, "#e5e7eb")))
                self.device_table.setItem(row, column, item)

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
            software_scan_interval_seconds=int(self.software_scan_interval.value()),
            usb_health_scan_interval_seconds=int(self.usb_health_scan_interval.value()),
        )
        self.controller.save_settings(self.settings)
        self._save_device_priorities()
        self.apply_theme()
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
                snap.addChild(node)
            self.advanced_tree.addTopLevelItem(snap)
        else:
            self.advanced_tree.addTopLevelItem(QTreeWidgetItem(["Snapshot", "Not saved yet"]))
        self.advanced_tree.expandToDepth(1)

    def show_and_raise(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
