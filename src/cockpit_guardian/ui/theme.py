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
        QWidget { color: #0f172a; font-size: 13px; }
        QLabel { background: transparent; }
        QWidget#AppBackground { background: #f8fafc; }
        QFrame#StatusBanner { border-radius: 8px; color: white; }
        QPushButton { background: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; }
        QPushButton:hover { background: #cbd5e1; }
        QPushButton#PrimaryButton { background: #2563eb; color: white; border-color: #2563eb; }
        QTabWidget::pane { background: rgba(248, 250, 252, 192); border: 1px solid #cbd5e1; border-radius: 6px; }
        QTabBar::tab { background: #e2e8f0; padding: 8px 14px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: white; }
        QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
            background: white; border: 1px solid #cbd5e1; border-radius: 6px;
        }
        QHeaderView::section { background: #e2e8f0; padding: 6px; border: 0; }
        """
    return """
    QWidget { color: #e5e7eb; font-size: 13px; }
    QLabel { background: transparent; }
    QWidget#AppBackground { background: #05070b; }
    QFrame#StatusBanner { border-radius: 8px; color: white; }
    QPushButton { background: #1f2937; border: 1px solid #374151; border-radius: 6px; padding: 8px 12px; }
    QPushButton:hover { background: #374151; }
    QPushButton#PrimaryButton { background: #2563eb; color: white; border-color: #2563eb; }
    QPushButton:disabled { color: #6b7280; background: #111827; }
    QTabWidget::pane { background: rgba(17, 24, 39, 188); border: 1px solid #374151; border-radius: 6px; }
    QTabBar::tab { background: #1f2937; padding: 8px 14px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
    QTabBar::tab:selected { background: #374151; }
    QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
        background: #0f172a; border: 1px solid #374151; border-radius: 6px;
    }
    QHeaderView::section { background: #1f2937; padding: 6px; border: 0; }
    """
