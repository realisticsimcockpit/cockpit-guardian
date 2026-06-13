from __future__ import annotations

from ..models import GlobalStatus, Severity


STATUS_COLORS = {
    GlobalStatus.CHECK_NOT_DONE: "#6b7280",
    GlobalStatus.COCKPIT_READY: "#16a34a",
    GlobalStatus.WARNING: "#f59e0b",
    GlobalStatus.RESTORE_NEEDED: "#f97316",
    GlobalStatus.CRITICAL_DEVICE_MISSING: "#dc2626",
}


SEVERITY_COLORS = {
    Severity.OK: "#16a34a",
    Severity.INFO: "#64748b",
    Severity.WARNING: "#f59e0b",
    Severity.RESTORE_NEEDED: "#f97316",
    Severity.CRITICAL: "#dc2626",
}


def app_stylesheet(theme: str = "dark") -> str:
    if theme == "light":
        return """
        QWidget { color: #f8fafc; font-size: 13px; }
        QLabel { background: transparent; }
        QWidget#AppBackground { background: #000000; }
        QFrame#DashboardHeader { background: rgba(0, 0, 0, 178); border: 0; border-radius: 4px; }
        QPushButton { background: rgba(15, 23, 42, 210); color: #f8fafc; border: 1px solid rgba(148, 163, 184, 72); border-radius: 4px; padding: 8px 12px; }
        QPushButton:hover { background: rgba(30, 41, 59, 232); }
        QPushButton#PrimaryButton { background: #2563eb; color: white; border-color: #2563eb; }
        QTabWidget::pane { background: transparent; border: 0; }
        QTabBar::tab { background: rgba(0, 0, 0, 178); color: #d1d5db; padding: 8px 14px; border: 0; }
        QTabBar::tab:selected { background: rgba(0, 0, 0, 235); color: white; border-bottom: 2px solid #dc0000; }
        QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
            background: rgba(0, 0, 0, 178); color: #f8fafc; border: 0; border-radius: 4px;
        }
        QHeaderView::section { background: rgba(0, 0, 0, 235); color: #f8fafc; padding: 6px; border: 0; }
        """
    return """
    QWidget { color: #e5e7eb; font-size: 13px; }
    QLabel { background: transparent; }
    QWidget#AppBackground { background: #000000; }
    QFrame#DashboardHeader { background: rgba(0, 0, 0, 178); border: 0; border-radius: 4px; }
    QPushButton { background: rgba(15, 23, 42, 210); border: 1px solid rgba(148, 163, 184, 72); border-radius: 4px; padding: 8px 12px; }
    QPushButton:hover { background: rgba(30, 41, 59, 232); }
    QPushButton#PrimaryButton { background: #2563eb; color: white; border-color: #2563eb; }
    QPushButton:disabled { color: #6b7280; background: rgba(15, 23, 42, 130); }
    QTabWidget::pane { background: transparent; border: 0; }
    QTabBar::tab { background: rgba(0, 0, 0, 178); color: #d1d5db; padding: 8px 14px; border: 0; }
    QTabBar::tab:selected { background: rgba(0, 0, 0, 235); color: white; border-bottom: 2px solid #dc0000; }
    QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
        background: rgba(0, 0, 0, 178); border: 0; border-radius: 4px; gridline-color: rgba(148, 163, 184, 45);
    }
    QHeaderView::section { background: rgba(0, 0, 0, 235); padding: 6px; border: 0; }
    """
