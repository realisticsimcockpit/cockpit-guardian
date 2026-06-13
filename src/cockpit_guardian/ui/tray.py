from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..models import CheckReport, GlobalStatus
from .theme import STATUS_COLORS


class GuardianTray(QObject):
    open_requested = Signal()
    check_requested = Signal()
    restore_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tray = QSystemTrayIcon(parent)
        self.tray.setIcon(self._icon(GlobalStatus.CHECK_NOT_DONE))
        self.tray.setToolTip("Check Not Done")
        menu = QMenu()
        open_action = QAction("Open Cockpit Guardian", self)
        check_action = QAction("Check Now", self)
        restore_action = QAction("Restore", self)
        exit_action = QAction("Exit", self)
        open_action.triggered.connect(self.open_requested.emit)
        check_action.triggered.connect(self.check_requested.emit)
        restore_action.triggered.connect(self.restore_requested.emit)
        exit_action.triggered.connect(self.exit_requested.emit)
        for action in [open_action, check_action, restore_action]:
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def update_report(self, report: CheckReport) -> None:
        self.tray.setIcon(self._icon(report.global_status))
        ok_count = sum(1 for check in report.device_checks if check.severity.value == "ok")
        issue_count = len(report.issues)
        if report.global_status == GlobalStatus.COCKPIT_READY:
            tooltip = f"Cockpit Ready - {ok_count} devices OK"
        elif report.global_status == GlobalStatus.CHECK_NOT_DONE:
            tooltip = "Check Not Done"
        else:
            tooltip = f"{report.global_status.value} - {issue_count} issues"
        self.tray.setToolTip(tooltip)

    def _activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_requested.emit()

    @staticmethod
    def _icon(status: GlobalStatus) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(STATUS_COLORS.get(status, "#6b7280")))
        painter.setPen(QColor("transparent"))
        painter.drawEllipse(8, 8, 48, 48)
        painter.end()
        return QIcon(pixmap)
