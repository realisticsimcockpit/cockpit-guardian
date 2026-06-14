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
        QWidget { color: #f8fafc; font-size: 11px; }
        QLabel { background: transparent; }
        QWidget#AppBackground { background: #000000; }
        QFrame#DashboardHeader { background: transparent; border: 0; }
        QFrame#DataPanel { background: rgba(0, 0, 0, 124); border: 1px solid rgba(148, 163, 184, 150); border-radius: 5px; }
        QLabel#PanelTitle { color: #f8fafc; font-size: 12px; font-weight: 700; }
        QWidget#SummaryContent { background: transparent; border: 0; }
        QLabel#ChecklistName { color: #f8fafc; font-size: 10px; }
        QLabel#ChecklistIcon { font-size: 12px; font-weight: 800; }
        QLabel#LogoCredit { color: #d1d5db; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
        QFrame#AppFooter { background: rgba(0, 0, 0, 150); border-top: 1px solid rgba(148, 163, 184, 110); }
        QLabel#FooterText { color: #ffffff; font-size: 10px; }
        QPushButton { background: rgba(0, 0, 0, 190); color: #f8fafc; border: 1px solid rgba(255, 255, 255, 90); border-radius: 5px; padding: 6px 10px; }
        QPushButton:hover { background: rgba(25, 25, 25, 235); border-color: rgba(220, 38, 38, 210); }
        QPushButton#PrimaryButton { background: rgba(185, 28, 28, 215); color: white; border-color: #ef4444; }
        QPushButton#LanguageButton { padding: 0; border: 1px solid rgba(255, 255, 255, 115); background: rgba(0, 0, 0, 190); }
        QPushButton#LanguageButton:checked { border: 1px solid #dc2626; background: rgba(220, 38, 38, 100); }
        QTabWidget::pane { background: transparent; border: 0; }
        QTabBar::tab { background: rgba(0, 0, 0, 178); color: #d1d5db; padding: 5px 10px; border: 0; }
        QTabBar::tab:selected { background: rgba(0, 0, 0, 235); color: white; border-bottom: 2px solid #dc0000; }
        QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
            background: rgba(0, 0, 0, 178); color: #f8fafc; border: 0; border-radius: 4px; gridline-color: rgba(255, 255, 255, 175);
        }
        QTableWidget { alternate-background-color: rgba(18, 18, 18, 220); }
        QTableWidget::item { padding-left: 3px; }
        QTableWidget::item:selected, QTreeWidget::item:selected { background: rgba(185, 28, 28, 150); color: #ffffff; }
        QHeaderView::section { background: rgba(0, 0, 0, 235); color: #f8fafc; padding: 4px 4px 4px 5px; border: 0; border-right: 1px solid rgba(255, 255, 255, 185); text-align: left; }
        QScrollBar:vertical { background: rgba(0, 0, 0, 120); width: 8px; margin: 0; }
        QScrollBar::handle:vertical { background: rgba(148, 163, 184, 150); min-height: 22px; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """
    return """
    QWidget { color: #e5e7eb; font-size: 11px; }
    QLabel { background: transparent; }
    QWidget#AppBackground { background: #000000; }
    QFrame#DashboardHeader { background: transparent; border: 0; }
    QFrame#DataPanel { background: rgba(0, 0, 0, 124); border: 1px solid rgba(148, 163, 184, 150); border-radius: 5px; }
    QLabel#PanelTitle { color: #f8fafc; font-size: 12px; font-weight: 700; }
    QWidget#SummaryContent { background: transparent; border: 0; }
    QLabel#ChecklistName { color: #f8fafc; font-size: 10px; }
    QLabel#ChecklistIcon { font-size: 12px; font-weight: 800; }
    QLabel#LogoCredit { color: #d1d5db; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
    QFrame#AppFooter { background: rgba(0, 0, 0, 150); border-top: 1px solid rgba(148, 163, 184, 110); }
    QLabel#FooterText { color: #ffffff; font-size: 10px; }
    QPushButton { background: rgba(0, 0, 0, 190); border: 1px solid rgba(255, 255, 255, 90); border-radius: 5px; padding: 6px 10px; }
    QPushButton:hover { background: rgba(25, 25, 25, 235); border-color: rgba(220, 38, 38, 210); }
    QPushButton#PrimaryButton { background: rgba(185, 28, 28, 215); color: white; border-color: #ef4444; }
    QPushButton#LanguageButton { padding: 0; border: 1px solid rgba(255, 255, 255, 115); background: rgba(0, 0, 0, 190); }
    QPushButton#LanguageButton:checked { border: 1px solid #dc2626; background: rgba(220, 38, 38, 100); }
    QPushButton:disabled { color: #6b7280; background: rgba(15, 23, 42, 130); }
    QTabWidget::pane { background: transparent; border: 0; }
    QTabBar::tab { background: rgba(0, 0, 0, 178); color: #d1d5db; padding: 5px 10px; border: 0; }
    QTabBar::tab:selected { background: rgba(0, 0, 0, 235); color: white; border-bottom: 2px solid #dc0000; }
    QTableWidget, QTreeWidget, QTextEdit, QLineEdit, QDoubleSpinBox, QComboBox {
        background: rgba(0, 0, 0, 178); border: 0; border-radius: 4px; gridline-color: rgba(255, 255, 255, 175);
    }
    QTableWidget { alternate-background-color: rgba(18, 18, 18, 220); }
    QTableWidget::item { padding-left: 3px; }
    QTableWidget::item:selected, QTreeWidget::item:selected { background: rgba(185, 28, 28, 150); color: #ffffff; }
    QHeaderView::section { background: rgba(0, 0, 0, 235); padding: 4px 4px 4px 5px; border: 0; border-right: 1px solid rgba(255, 255, 255, 185); text-align: left; }
    QScrollBar:vertical { background: rgba(0, 0, 0, 120); width: 8px; margin: 0; }
    QScrollBar::handle:vertical { background: rgba(148, 163, 184, 150); min-height: 22px; border-radius: 4px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    """
