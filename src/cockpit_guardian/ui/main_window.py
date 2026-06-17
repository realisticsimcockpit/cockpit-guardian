from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QRectF, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen, QPixmap
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
    QInputDialog,
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
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..controller import AppController
from ..models import CheckReport, DeviceBus, DeviceKind, GlobalStatus, Priority, RestoreReport, Settings, Severity, SoftwareState
from .assets import asset_icon, asset_pixmap
from .theme import SEVERITY_COLORS, STATUS_COLORS, app_stylesheet
from .tray import GuardianTray


WINDOW_WIDTH = 905
WINDOW_HEIGHT = 679
YOUTUBE_URL = "https://www.youtube.com/@realisticsimcockpit"
CHECKLIST_ROWS_PER_COLUMN = 8
CHECKLIST_COLUMNS = 3
CHECKLIST_COLUMN_WIDTH = 122
STATUS_ICON_SIZE = 13
LOGO_LOCKUP_WIDTH = 186
STATUS_BLOCK_WIDTH = 344

DASHBOARD_TEXT = {
    "en": {
        "logo_credit": "by REALISTIC SIMCOCKPIT",
        "footer_prefix": "Author:",
        "footer_version": "Version",
        "language_en_tooltip": "Switch dashboard language to English",
        "language_fr_tooltip": "Switch dashboard language to French",
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
            DeviceKind.WHEEL: "Wheel base",
            DeviceKind.STEERING_WHEEL: "Steering wheel",
            DeviceKind.PEDALS: "Pedals",
            DeviceKind.ACTIVE_PEDAL: "DIY Active Pedal",
            DeviceKind.SHIFTER: "Shifter",
            DeviceKind.HANDBRAKE: "Handbrake",
            DeviceKind.BUTTON_BOX: "Button Box",
            DeviceKind.DDU: "DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Wind Simulator",
            DeviceKind.SEAT_MOVER: "SeatMover",
            DeviceKind.AMBILIGHT: "Ambilight",
            DeviceKind.OTHER: "Other",
        },
        "checklist_device_kinds": {
            DeviceKind.WHEEL: "Wheel base",
            DeviceKind.STEERING_WHEEL: "Steering wheel",
            DeviceKind.PEDALS: "Pedals",
            DeviceKind.ACTIVE_PEDAL: "DIY Active Pedal",
            DeviceKind.SHIFTER: "Shifter",
            DeviceKind.HANDBRAKE: "Handbrake",
            DeviceKind.BUTTON_BOX: "Button box",
            DeviceKind.DDU: "DDU display",
            DeviceKind.ARDUINO_SIMHUB: "SimHub Arduino",
            DeviceKind.WIND_SIMULATOR: "Wind",
            DeviceKind.SEAT_MOVER: "SeatMover",
            DeviceKind.AMBILIGHT: "Ambilight",
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
        "usb_speed_scan": "USB Speed Scan",
        "rollback": "Rollback",
        "export": "Export",
        "import": "Import",
        "export_config_tooltip": "Choose a cloud-synced folder such as OneDrive, Google Drive, Dropbox, iCloud, or a NAS.",
        "import_config_tooltip": "Import this backup after reinstalling Windows, then run Restore.",
        "device_headers": ["Device", "Role", "Status", "USB"],
        "joystick_order": "Joystick Order",
        "joystick_order_hint": "Use Up / Down to set desired order",
        "joystick_headers": ["Win #", "Joystick", "Saved #", "USB"],
        "joystick_move_up": "Up",
        "joystick_move_down": "Down",
        "joystick_properties": "Properties",
        "joystick_select_first": "Select a joystick first.",
        "joystick_properties_failed": "Could not open joystick properties.",
        "usb_health": "USB",
        "usb_health_tab": "USB Health",
        "usb_health_score": "Stability score: {score}",
        "usb_health_headers": ["Time", "Severity", "Device", "Event"],
        "quick_log": "Quick log",
        "no_quick_log": "No recent event",
        "last_ffb_clipping": "Last FFB Clipping at {time}",
        "last_usb_disconnect": "Last USB disconnect at {time}",
        "refresh_logs": "Refresh Logs",
        "export_logs": "Export Logs",
        "clear_logs": "Clear Logs",
        "logs_exported": "Logs exported to {path}.",
        "clear_logs_confirm": "Clear the current log file?",
        "clear_logs_done": "Logs cleared.",
        "log_file_filter": "Log files (*.log);;Text files (*.txt)",
        "settings": "Settings",
        "active_profile": "Active profile",
        "ffb_threshold": "FFB clipping threshold",
        "notifications": "Notifications",
        "launch_startup": "Launch at Windows startup",
        "auto_restore": "Auto-restore",
        "simhub_required": "SimHub is required",
        "deep_windows_scan": "Deep Windows scan",
        "software_scan_cache": "Software scan cache",
        "usb_health_cache": "USB Health cache",
        "theme": "Theme",
        "language": "Language",
        "save_settings": "Save Settings",
        "settings_saved": "Settings saved.",
        "device_priority": "Device priority",
        "priority_headers": ["Device", "Role", "Priority"],
        "priority_labels": {
            Priority.REQUIRED: "Required",
            Priority.OPTIONAL: "Optional",
            Priority.IGNORED: "Ignored",
        },
        "theme_labels": {"dark": "Dark", "light": "Light"},
        "no_saved_config": "No saved configuration yet",
        "edit_role_title": "Edit Role",
        "edit_role_label": "Role:",
        "usb_speed_scan_title": "USB Speed Scan",
        "usb_speed_scan_done": "USB speed scan complete. {count} USB port records cached.",
        "export_config_title": "Export Config Backup",
        "import_config_title": "Import Config Backup",
        "config_backup_filter": "Cockpit Guardian backup (*.json);;JSON files (*.json)",
        "import_config_confirm": "Importing will replace the current saved configuration after creating a local safety backup. Continue?",
        "export_config_done": "Configuration backup exported to:\n{path}\n\nStore this file in a cloud-synced folder before reinstalling Windows.",
        "import_config_done": "Configuration imported. A local safety backup was created at:\n{path}\n\nRun Restore if the check reports changed COM ports or joystick order.",
        "restore_title": "Restore",
        "rollback_title": "Rollback Last Restore",
        "busy_default": "Working",
        "busy_save": "Saving configuration",
        "busy_check": "Checking cockpit",
        "busy_restore": "Restoring cockpit",
        "busy_usb_speed_scan": "Scanning USB speeds",
        "busy_rollback": "Rolling back restore",
        "busy_export": "Exporting backup",
        "busy_import": "Importing backup",
        "ffb_clipping_detail": "FFB clipping {percent:.0f}% - Reduce in-game FFB gain",
        "usb_labels": {
            "USB 3.x capable path": "USB 3.x capable path",
            "USB 2.0 path": "USB 2.0 path",
            "USB 1.x/full-speed path": "USB 1.x/full-speed path",
            "USB serial bridge": "USB serial bridge",
            "USB speed unknown": "USB speed unknown",
            "USB speed scan needed": "USB speed scan needed",
        },
        "usb_sources": {
            "Arduino USB Serial": "Arduino USB Serial",
            "Silicon Labs CP210x USB-to-UART bridge": "Silicon Labs CP210x",
            "WCH CH340 USB serial bridge": "WCH CH340",
            "WCH CH341 USB serial bridge": "WCH CH341",
            "WCH CH343 USB serial bridge": "WCH CH343",
            "WCH CH9102 USB serial bridge": "WCH CH9102",
            "FTDI FT232 USB serial bridge": "FTDI FT232",
            "FTDI USB serial bridge": "FTDI",
            "Prolific PL2303 USB serial bridge": "Prolific PL2303",
            "Espressif USB JTAG/serial bridge": "Espressif USB JTAG/serial",
        },
        "tabs": ["Dashboard", "USB Health", "Logs", "Settings"],
    },
    "fr": {
        "logo_credit": "par REALISTIC SIMCOCKPIT",
        "footer_prefix": "Auteur :",
        "footer_version": "Version",
        "language_en_tooltip": "Basculer le dashboard en anglais",
        "language_fr_tooltip": "Basculer le dashboard en français",
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
            DeviceKind.WHEEL: "Base volant",
            DeviceKind.STEERING_WHEEL: "Volant",
            DeviceKind.PEDALS: "Pédales",
            DeviceKind.ACTIVE_PEDAL: "DIY Active Pedal",
            DeviceKind.SHIFTER: "Boîte",
            DeviceKind.HANDBRAKE: "Frein à main",
            DeviceKind.BUTTON_BOX: "Boîtier boutons",
            DeviceKind.DDU: "DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Ventilation",
            DeviceKind.SEAT_MOVER: "SeatMover",
            DeviceKind.AMBILIGHT: "Ambilight",
            DeviceKind.OTHER: "Autre",
        },
        "checklist_device_kinds": {
            DeviceKind.WHEEL: "Base volant",
            DeviceKind.STEERING_WHEEL: "Volant",
            DeviceKind.PEDALS: "Pédalier",
            DeviceKind.ACTIVE_PEDAL: "DIY Active Pedal",
            DeviceKind.SHIFTER: "Boîte",
            DeviceKind.HANDBRAKE: "Frein à main",
            DeviceKind.BUTTON_BOX: "Boîtier boutons",
            DeviceKind.DDU: "Écran DDU",
            DeviceKind.ARDUINO_SIMHUB: "Arduino SimHub",
            DeviceKind.WIND_SIMULATOR: "Ventilation",
            DeviceKind.SEAT_MOVER: "SeatMover",
            DeviceKind.AMBILIGHT: "Ambilight",
            DeviceKind.OTHER: "Périphérique",
        },
        "software_group": "Logiciels",
        "unknown": "Inconnu",
        "detected_com_status": "{com} détecté",
        "com_mismatch_status": "Attendu {expected}, détecté {detected}",
        "missing_device": "Absent",
        "com_ports": "Ports COM",
        "save": "Enregistrer",
        "check": "Vérifier",
        "restore": "Restaurer",
        "usb_speed_scan": "Scan vitesse USB",
        "rollback": "Annuler",
        "export": "Exporter",
        "import": "Importer",
        "export_config_tooltip": "Choisissez un dossier synchronisé cloud comme OneDrive, Google Drive, Dropbox, iCloud ou un NAS.",
        "import_config_tooltip": "Importez cette sauvegarde après une réinstallation de Windows, puis lancez Restaurer.",
        "device_headers": ["Périphérique", "Rôle", "Statut", "USB"],
        "joystick_order": "Ordre joysticks",
        "joystick_order_hint": "Utilisez Monter / Descendre pour choisir l'ordre souhaité",
        "joystick_headers": ["Win #", "Joystick", "Sauvé #", "USB"],
        "joystick_move_up": "Monter",
        "joystick_move_down": "Descendre",
        "joystick_properties": "Propriétés",
        "joystick_select_first": "Sélectionnez d'abord un joystick.",
        "joystick_properties_failed": "Impossible d'ouvrir les propriétés du joystick.",
        "usb_health": "USB",
        "usb_health_tab": "Santé USB",
        "usb_health_score": "Score de stabilité : {score}",
        "usb_health_headers": ["Heure", "Sévérité", "Périphérique", "Événement"],
        "quick_log": "Journal rapide",
        "no_quick_log": "Aucun événement récent",
        "last_ffb_clipping": "Dernier écrêtage FFB à {time}",
        "last_usb_disconnect": "Dernière déconnexion USB à {time}",
        "refresh_logs": "Rafraîchir les logs",
        "export_logs": "Exporter les logs",
        "clear_logs": "Effacer les logs",
        "logs_exported": "Logs exportés vers {path}.",
        "clear_logs_confirm": "Effacer le fichier de logs actuel ?",
        "clear_logs_done": "Logs effacés.",
        "log_file_filter": "Fichiers log (*.log);;Fichiers texte (*.txt)",
        "settings": "Réglages",
        "active_profile": "Profil actif",
        "ffb_threshold": "Seuil écrêtage FFB",
        "notifications": "Notifications",
        "launch_startup": "Lancer au démarrage de Windows",
        "auto_restore": "Restauration automatique",
        "simhub_required": "SimHub est requis",
        "deep_windows_scan": "Scan Windows profond",
        "software_scan_cache": "Cache scan logiciels",
        "usb_health_cache": "Cache santé USB",
        "theme": "Thème",
        "language": "Langue",
        "save_settings": "Enregistrer les réglages",
        "settings_saved": "Réglages enregistrés.",
        "device_priority": "Priorité des périphériques",
        "priority_headers": ["Périphérique", "Rôle", "Priorité"],
        "priority_labels": {
            Priority.REQUIRED: "Requis",
            Priority.OPTIONAL: "Optionnel",
            Priority.IGNORED: "Ignoré",
        },
        "theme_labels": {"dark": "Sombre", "light": "Clair"},
        "no_saved_config": "Aucune configuration enregistrée",
        "edit_role_title": "Modifier le rôle",
        "edit_role_label": "Rôle :",
        "usb_speed_scan_title": "Scan vitesse USB",
        "usb_speed_scan_done": "Scan vitesse USB terminé. {count} ports USB mémorisés.",
        "export_config_title": "Exporter la sauvegarde",
        "import_config_title": "Importer une sauvegarde",
        "config_backup_filter": "Sauvegarde Cockpit Guardian (*.json);;Fichiers JSON (*.json)",
        "import_config_confirm": "L'import remplacera la configuration actuelle après création d'une sauvegarde locale. Continuer ?",
        "export_config_done": "Sauvegarde exportée vers :\n{path}\n\nStockez ce fichier dans un dossier synchronisé cloud avant de réinstaller Windows.",
        "import_config_done": "Configuration importée. Une sauvegarde locale a été créée ici :\n{path}\n\nLancez Restaurer si le contrôle signale des ports COM ou un ordre joystick modifiés.",
        "restore_title": "Restaurer",
        "rollback_title": "Annuler la dernière restauration",
        "busy_default": "Traitement en cours",
        "busy_save": "Enregistrement de la configuration",
        "busy_check": "Vérification du cockpit",
        "busy_restore": "Restauration du cockpit",
        "busy_usb_speed_scan": "Scan des vitesses USB",
        "busy_rollback": "Annulation de la restauration",
        "busy_export": "Export de la sauvegarde",
        "busy_import": "Import de la sauvegarde",
        "ffb_clipping_detail": "Écrêtage FFB {percent:.0f}% - réduisez le gain FFB dans le jeu",
        "usb_labels": {
            "USB 3.x capable path": "Chemin compatible USB 3.x",
            "USB 2.0 path": "Chemin USB 2.0",
            "USB 1.x/full-speed path": "Chemin USB 1.x / pleine vitesse",
            "USB serial bridge": "Pont série USB",
            "USB speed unknown": "Vitesse USB inconnue",
            "USB speed scan needed": "Scan vitesse USB requis",
        },
        "usb_sources": {
            "Arduino USB Serial": "Arduino",
            "Silicon Labs CP210x USB-to-UART bridge": "Silicon Labs CP210x",
            "WCH CH340 USB serial bridge": "WCH CH340",
            "WCH CH341 USB serial bridge": "WCH CH341",
            "WCH CH343 USB serial bridge": "WCH CH343",
            "WCH CH9102 USB serial bridge": "WCH CH9102",
            "FTDI FT232 USB serial bridge": "FTDI FT232",
            "FTDI USB serial bridge": "FTDI",
            "Prolific PL2303 USB serial bridge": "Prolific PL2303",
            "Espressif USB JTAG/serial bridge": "Espressif USB JTAG/série",
        },
        "tabs": ["Dashboard", "Santé USB", "Logs", "Réglages"],
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


class StatusIconLabel(QLabel):
    def __init__(self, severity: Severity | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._severity = severity
        self.setFixedSize(STATUS_ICON_SIZE, STATUS_ICON_SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("")

    def set_severity(self, severity: Severity) -> None:
        self._severity = severity
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._severity is None:
            event.accept()
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(SEVERITY_COLORS.get(self._severity, "#e5e7eb"))
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        width = float(self.width())
        height = float(self.height())

        if self._severity == Severity.OK:
            painter.drawLine(QPointF(width * 0.22, height * 0.56), QPointF(width * 0.43, height * 0.75))
            painter.drawLine(QPointF(width * 0.43, height * 0.75), QPointF(width * 0.80, height * 0.26))
        elif self._severity == Severity.CRITICAL:
            painter.drawLine(QPointF(width * 0.20, height * 0.20), QPointF(width * 0.80, height * 0.80))
            painter.drawLine(QPointF(width * 0.80, height * 0.20), QPointF(width * 0.20, height * 0.80))
        else:
            painter.drawLine(QPointF(width * 0.50, height * 0.18), QPointF(width * 0.80, height * 0.78))
            painter.drawLine(QPointF(width * 0.80, height * 0.78), QPointF(width * 0.20, height * 0.78))
            painter.drawLine(QPointF(width * 0.20, height * 0.78), QPointF(width * 0.50, height * 0.18))
            painter.drawLine(QPointF(width * 0.50, height * 0.38), QPointF(width * 0.50, height * 0.57))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(width * 0.50, height * 0.67), 0.9, 0.9)
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


class JoystickOrderTableWidget(SeparatorTableWidget):
    order_changed = Signal(list)

    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def move_current_row(self, delta: int) -> bool:
        source_row = self.currentRow()
        if source_row < 0 or source_row >= self.rowCount():
            return False
        if self.item(source_row, 0) and self.item(source_row, 0).text() == "-":
            return False
        target_row = max(0, min(source_row + delta, self.rowCount() - 1))
        if target_row == source_row:
            return True
        self._move_row(source_row, target_row)
        self.order_changed.emit(self.current_order())
        return True

    def _move_row(self, source_row: int, target_row: int) -> None:
        rows = self._row_items()
        if source_row < 0 or source_row >= len(rows):
            return
        row_items = rows.pop(source_row)
        target_row = max(0, min(target_row, len(rows)))
        rows.insert(target_row, row_items)
        self.setRowCount(0)
        for values in rows:
            row = self.rowCount()
            self.insertRow(row)
            for column, item in enumerate(values):
                self.setItem(row, column, item)
        self.setCurrentCell(target_row, 0)

    def _row_items(self) -> list[list[QTableWidgetItem]]:
        rows = []
        for row in range(self.rowCount()):
            values = []
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is None:
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item = item.clone()
                values.append(item)
            rows.append(values)
        return rows

    def current_order(self) -> list[str]:
        return [
            self.item(row, 1).text()
            for row in range(self.rowCount())
            if self.item(row, 1) and self.item(row, 1).text() and self.item(row, 0) and self.item(row, 0).text() != "-"
        ]


class BusyOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._message = ""
        self._progress = 0
        self.hide()

    def show_progress(self, message: str, progress: int = 0) -> None:
        self._message = message
        self._progress = max(0, min(100, progress))
        self.show()
        self.raise_()
        self.update()

    def set_progress(self, progress: int) -> None:
        self._progress = max(0, min(100, progress))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 138))

        panel_width = min(460, max(340, self.width() - 80))
        panel_height = 150
        panel = QRectF(
            (self.width() - panel_width) / 2,
            (self.height() - panel_height) / 2,
            panel_width,
            panel_height,
        )
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
        painter.setBrush(QColor(0, 0, 0, 230))
        painter.drawRoundedRect(panel, 6, 6)

        title_font = painter.font()
        title_font.setBold(True)
        title_font.setPointSize(12)
        painter.setFont(title_font)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(panel.adjusted(18, 18, -18, -92), Qt.AlignmentFlag.AlignCenter, self._message.upper())

        led_count = 18
        led_gap = 4
        led_height = 18
        led_total_gap = led_gap * (led_count - 1)
        led_width = (panel.width() - 40 - led_total_gap) / led_count
        led_y = panel.y() + 74
        active_count = round((self._progress / 100) * led_count)
        for index in range(led_count):
            if index >= active_count:
                color = QColor(35, 35, 35)
            elif index >= 14:
                color = QColor("#ef4444")
            elif index >= 10:
                color = QColor("#facc15")
            else:
                color = QColor("#22c55e")
            led = QRectF(panel.x() + 20 + index * (led_width + led_gap), led_y, led_width, led_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(led, 2, 2)

        percent_font = painter.font()
        percent_font.setBold(True)
        percent_font.setPointSize(16)
        painter.setFont(percent_font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(panel.adjusted(0, 102, 0, -14), Qt.AlignmentFlag.AlignCenter, f"{self._progress}%")
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
        self._busy_progress = 0

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
        self.busy_overlay = BusyOverlay(self.background)
        self.busy_overlay.setGeometry(self.background.rect())
        self.busy_progress_timer = QTimer(self)
        self.busy_progress_timer.setInterval(90)
        self.busy_progress_timer.timeout.connect(self._advance_busy_progress)
        self._build_dashboard()
        self._build_usb_health_tab()
        self._build_logs_tab()
        self._build_settings_tab()
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
        self._game_controller_signature = self.controller.game_controller_signature()
        self.device_watch_timer = QTimer(self)
        self.device_watch_timer.setInterval(1500)
        self.device_watch_timer.timeout.connect(self._poll_game_controllers)
        self.device_watch_timer.start()
        self.device_change_rescan_timer = QTimer(self)
        self.device_change_rescan_timer.setSingleShot(True)
        self.device_change_rescan_timer.timeout.connect(self._auto_scan_usb_after_device_change)
        QTimer.singleShot(250, self.check_now)
        QTimer.singleShot(1200, self._initial_usb_speed_scan)

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(app_stylesheet(self.settings.theme))

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        if hasattr(self, "busy_overlay"):
            self.busy_overlay.setGeometry(self.background.rect())
        self._resize_dashboard_columns()

    def _resize_dashboard_columns(self) -> None:
        if not hasattr(self, "device_table"):
            return
        self._set_table_column_widths(self.device_table, [0.24, 0.20, 0.28, 0.28])
        self._set_table_column_widths(self.joystick_table, [0.08, 0.34, 0.12, 0.46])
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
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table.verticalHeader().setDefaultSectionSize(24)
        table.verticalHeader().setMinimumSectionSize(22)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    @staticmethod
    def _set_table_headers(table: QTableWidget, labels: list[str]) -> None:
        for column, label in enumerate(labels):
            item = QTableWidgetItem(label)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
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
        logo_block.setMinimumWidth(STATUS_BLOCK_WIDTH)
        logo_block.setMaximumWidth(STATUS_BLOCK_WIDTH)
        logo_layout = QVBoxLayout(logo_block)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)
        self.dashboard_logo = QLabel()
        self.dashboard_logo.setObjectName("DashboardLogo")
        self.dashboard_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = asset_pixmap("ui_logo_cg.png")
        if not logo.isNull():
            self.dashboard_logo.setPixmap(
                logo.scaled(
                    LOGO_LOCKUP_WIDTH,
                    55,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.dashboard_logo.setFixedSize(LOGO_LOCKUP_WIDTH, 56)
        self.logo_credit_label = QLabel()
        self.logo_credit_label.setObjectName("LogoCredit")
        self.logo_credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_credit_label.setFixedSize(LOGO_LOCKUP_WIDTH, 12)
        self.status_title = QLabel("CHECK NOT DONE")
        self.status_title.setObjectName("StatusTitle")
        self.status_title.setFixedWidth(STATUS_BLOCK_WIDTH)
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_layout.addWidget(self.dashboard_logo)
        logo_layout.addWidget(self.logo_credit_label)
        logo_layout.addSpacing(4)
        logo_layout.addWidget(self.status_title)
        self.usb_status_row = QWidget()
        self.usb_status_row.setObjectName("StatusMetric")
        usb_status_layout = QHBoxLayout(self.usb_status_row)
        usb_status_layout.setContentsMargins(0, 0, 0, 0)
        usb_status_layout.setSpacing(3)
        self.usb_status_label = QLabel()
        self.usb_status_label.setObjectName("StatusMetricLabel")
        self.usb_status_icon = StatusIconLabel()
        self.usb_status_icon.setObjectName("StatusMetricIcon")
        usb_status_layout.addWidget(self.usb_status_label)
        usb_status_layout.addWidget(self.usb_status_icon)
        usb_status_layout.addStretch(1)
        self.usb_status_row.setVisible(False)
        logo_layout.addWidget(self.usb_status_row)
        logo_layout.addStretch(1)
        header_layout.addWidget(logo_block, 1, Qt.AlignmentFlag.AlignTop)

        self.summary_content = QWidget()
        self.summary_content.setObjectName("SummaryContent")
        self.summary_content.setMinimumWidth(CHECKLIST_COLUMN_WIDTH * CHECKLIST_COLUMNS + 36)
        self.summary_content.setMaximumWidth(456)
        self.summary_checklist_layout = QGridLayout(self.summary_content)
        self.summary_checklist_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_checklist_layout.setHorizontalSpacing(18)
        self.summary_checklist_layout.setVerticalSpacing(0)
        for column in range(CHECKLIST_COLUMNS):
            self.summary_checklist_layout.setColumnMinimumWidth(column, CHECKLIST_COLUMN_WIDTH)
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
        self.language_eng_button.setIconSize(QSize(21, 11))
        self.language_eng_button.setFixedSize(25, 14)
        self.language_eng_button.setToolTip(self._dashboard_text("language_en_tooltip"))
        self.language_eng_button.clicked.connect(lambda: self._set_language("en"))
        self.language_fr_button = QPushButton()
        self.language_fr_button.setObjectName("LanguageButton")
        self.language_fr_button.setCheckable(True)
        self.language_fr_button.setIcon(asset_icon("lang_fr.png"))
        self.language_fr_button.setIconSize(QSize(21, 11))
        self.language_fr_button.setFixedSize(25, 14)
        self.language_fr_button.setToolTip(self._dashboard_text("language_fr_tooltip"))
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
        self.usb_speed_scan_button = QPushButton("USB Speed Scan")
        self.rollback_button = QPushButton("Rollback")
        self.export_config_button = QPushButton("Export")
        self.import_config_button = QPushButton("Import")
        self.save_button.clicked.connect(self.save_configuration)
        self.check_button.clicked.connect(self.check_now)
        self.restore_button.clicked.connect(self.restore)
        self.usb_speed_scan_button.clicked.connect(self.scan_usb_speeds)
        self.rollback_button.clicked.connect(self.rollback)
        self.export_config_button.clicked.connect(self.export_config_backup)
        self.import_config_button.clicked.connect(self.import_config_backup)
        self.export_config_button.setToolTip(self._dashboard_text("export_config_tooltip"))
        self.import_config_button.setToolTip(self._dashboard_text("import_config_tooltip"))
        for index, button in enumerate(
            [
                self.save_button,
                self.check_button,
                self.restore_button,
                self.usb_speed_scan_button,
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
        self.device_table.cellDoubleClicked.connect(self._device_table_cell_double_clicked)
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self._device_table_context_requested)
        self.com_ports_panel = self._panel("COM Ports", self.device_table)
        self.com_ports_panel_title = self.com_ports_panel.title_label
        self.com_ports_panel_icon = self.com_ports_panel.title_icon
        tables.addWidget(self.com_ports_panel, 3)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)

        self.joystick_table = JoystickOrderTableWidget(0, 4)
        self._set_table_headers(self.joystick_table, ["Win #", "Joystick", "Saved #", "USB"])
        self._configure_table(self.joystick_table)
        self.joystick_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.joystick_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.joystick_table.order_changed.connect(self._joystick_order_changed)
        self.joystick_table.cellDoubleClicked.connect(lambda row, _column: self.open_selected_joystick_properties(row))
        joystick_content = QWidget()
        joystick_layout = QVBoxLayout(joystick_content)
        joystick_layout.setContentsMargins(0, 0, 0, 0)
        joystick_layout.setSpacing(6)
        joystick_layout.addWidget(self.joystick_table)
        joystick_controls = QHBoxLayout()
        joystick_controls.setContentsMargins(0, 0, 0, 0)
        joystick_controls.setSpacing(6)
        self.joystick_up_button = QPushButton("Up")
        self.joystick_down_button = QPushButton("Down")
        self.joystick_properties_button = QPushButton("Properties")
        self.joystick_up_button.clicked.connect(lambda: self._move_selected_joystick(-1))
        self.joystick_down_button.clicked.connect(lambda: self._move_selected_joystick(1))
        self.joystick_properties_button.clicked.connect(lambda: self.open_selected_joystick_properties())
        joystick_controls.addWidget(self.joystick_up_button)
        joystick_controls.addWidget(self.joystick_down_button)
        joystick_controls.addWidget(self.joystick_properties_button)
        joystick_controls.addStretch(1)
        joystick_layout.addLayout(joystick_controls)
        self.joystick_panel = self._panel("Joystick Order", joystick_content, subtitle=self._dashboard_text("joystick_order_hint"))
        self.joystick_panel_title = self.joystick_panel.title_label
        self.joystick_panel_subtitle = self.joystick_panel.subtitle_label
        self.joystick_panel_icon = self.joystick_panel.title_icon
        bottom_row.addWidget(self.joystick_panel, 3)

        self.quick_log_content = QWidget()
        self.quick_log_content.setObjectName("QuickLogContent")
        quick_log_layout = QVBoxLayout(self.quick_log_content)
        quick_log_layout.setContentsMargins(2, 2, 2, 2)
        quick_log_layout.setSpacing(5)
        self.quick_log_labels = []
        for _ in range(2):
            label = QLabel()
            label.setObjectName("QuickLogLine")
            label.setWordWrap(False)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            quick_log_layout.addWidget(label)
            self.quick_log_labels.append(label)
        quick_log_layout.addStretch(1)
        self.quick_log_panel = self._panel("Quick log", self.quick_log_content, show_icon=False)
        self.quick_log_panel_title = self.quick_log_panel.title_label
        bottom_row.addWidget(self.quick_log_panel, 1)

        tables.addLayout(bottom_row, 2)
        layout.addLayout(tables, 1)

        self.tabs.addTab(page, self._dashboard_text("tabs")[0])

    def _build_usb_health_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.usb_score = QLabel(self._dashboard_text("usb_health_score").format(score=100))
        self.usb_score.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(self.usb_score)
        self.usb_table = SeparatorTableWidget(0, 4)
        self._set_table_headers(self.usb_table, self._dashboard_text("usb_health_headers"))
        self._configure_table(self.usb_table)
        self.usb_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.usb_table)
        self.tabs.addTab(page, self._dashboard_text("tabs")[1])

    def _build_logs_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        button_layout = QHBoxLayout()
        self.refresh_logs_button = QPushButton(self._dashboard_text("refresh_logs"))
        self.export_logs_button = QPushButton(self._dashboard_text("export_logs"))
        self.clear_logs_button = QPushButton(self._dashboard_text("clear_logs"))
        self.refresh_logs_button.clicked.connect(self.refresh_logs)
        self.export_logs_button.clicked.connect(self.export_logs)
        self.clear_logs_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.refresh_logs_button)
        button_layout.addWidget(self.export_logs_button)
        button_layout.addWidget(self.clear_logs_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        self.tabs.addTab(page, self._dashboard_text("tabs")[2])
        self.refresh_logs()

    def _build_settings_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.settings_form = form
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
        for value, label in self._dashboard_text("theme_labels").items():
            self.theme_select.addItem(label, value)
        self._set_combo_data(self.theme_select, self.settings.theme)
        self.language_select = QComboBox()
        self.language_select.addItems(["en", "fr"])
        self.language_select.setCurrentText(self.settings.language)
        form.addRow(self._dashboard_text("active_profile"), self.profile_input)
        form.addRow(self._dashboard_text("ffb_threshold"), self.ffb_threshold)
        form.addRow(self._dashboard_text("notifications"), self.notifications)
        form.addRow(self._dashboard_text("launch_startup"), self.launch_startup)
        form.addRow(self._dashboard_text("auto_restore"), self.auto_restore)
        form.addRow(self._dashboard_text("simhub_required"), self.simhub_required)
        form.addRow(self._dashboard_text("deep_windows_scan"), self.deep_windows_scan)
        form.addRow(self._dashboard_text("software_scan_cache"), self.software_scan_interval)
        form.addRow(self._dashboard_text("usb_health_cache"), self.usb_health_scan_interval)
        form.addRow(self._dashboard_text("theme"), self.theme_select)
        form.addRow(self._dashboard_text("language"), self.language_select)
        layout.addLayout(form)

        self.save_settings_button = QPushButton(self._dashboard_text("save_settings"))
        self.save_settings_button.setObjectName("PrimaryButton")
        self.save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_button)

        self.priority_label = QLabel(self._dashboard_text("device_priority"))
        self.priority_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(self.priority_label)
        self.priority_table = SeparatorTableWidget(0, 3)
        self._set_table_headers(self.priority_table, self._dashboard_text("priority_headers"))
        self._configure_table(self.priority_table)
        self.priority_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.priority_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.priority_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.priority_table)
        self._load_priority_table()
        layout.addStretch(1)
        self.tabs.addTab(page, self._dashboard_text("tabs")[3])

    def _panel(self, title: str, child: QWidget, show_icon: bool = True, subtitle: str | None = None) -> QWidget:
        panel = QFrame()
        panel.setObjectName("DataPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("PanelTitle")
        subtitle_label = QLabel(subtitle or "")
        subtitle_label.setObjectName("PanelSubtitle")
        subtitle_label.setVisible(bool(subtitle))
        icon = StatusIconLabel()
        icon.setObjectName("PanelTitleIcon")
        icon.setVisible(show_icon)
        title_layout.addWidget(label)
        title_layout.addWidget(icon)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch(1)
        layout.addLayout(title_layout)
        layout.addWidget(child)
        panel.title_label = label
        panel.subtitle_label = subtitle_label
        panel.title_icon = icon
        return panel

    def _run_async(self, fn, callback, busy_text: str | None = None) -> None:
        self._show_busy_overlay(busy_text or self._dashboard_text("busy_default"), reset=self._busy_operations == 0)
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

    def _run_background_async(self, fn, callback=None) -> None:
        thread = QThread(self)
        worker = Worker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        if callback is not None:
            worker.finished.connect(callback)
        worker.failed.connect(lambda message: self.controller.logger.warning("Background operation failed: %s", message))
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._finish_background_thread(thread))
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        self._workers[thread] = worker
        thread.start()

    def _finish_thread(self, thread: QThread) -> None:
        self._busy_operations = max(0, self._busy_operations - 1)
        self._set_busy(self._busy_operations > 0)
        if thread in self._threads:
            self._threads.remove(thread)
        self._workers.pop(thread, None)
        if self._busy_operations == 0:
            self._complete_busy_overlay()

    def _finish_background_thread(self, thread: QThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        self._workers.pop(thread, None)

    def _set_busy(self, busy: bool) -> None:
        for button in [
            self.save_button,
            self.check_button,
            self.restore_button,
            self.usb_speed_scan_button,
            self.rollback_button,
            self.export_config_button,
            self.import_config_button,
            self.joystick_up_button,
            self.joystick_down_button,
            self.joystick_properties_button,
        ]:
            button.setDisabled(busy)

    def _show_busy_overlay(self, message: str, reset: bool = True) -> None:
        if reset:
            self._busy_progress = 4
        self.busy_overlay.show_progress(message, self._busy_progress)
        if not self.busy_progress_timer.isActive():
            self.busy_progress_timer.start()

    def _advance_busy_progress(self) -> None:
        if self._busy_operations <= 0:
            return
        if self._busy_progress < 92:
            self._busy_progress += max(1, round((92 - self._busy_progress) * 0.08))
            self.busy_overlay.set_progress(self._busy_progress)

    def _complete_busy_overlay(self) -> None:
        self.busy_progress_timer.stop()
        self._busy_progress = 100
        self.busy_overlay.set_progress(100)
        QTimer.singleShot(250, self._hide_busy_overlay_if_idle)

    def _hide_busy_overlay_if_idle(self) -> None:
        if self._busy_operations == 0:
            self.busy_overlay.hide()

    def save_configuration(self) -> None:
        self._run_async(self.controller.save_configuration, self._save_configuration_finished, self._dashboard_text("busy_save"))

    def _save_configuration_finished(self, _) -> None:
        self.check_now()

    def check_now(self) -> None:
        self._run_async(self.controller.check_now, self.update_report, self._dashboard_text("busy_check"))

    def restore(self) -> None:
        self._run_async(self.controller.restore, self._restore_finished, self._dashboard_text("busy_restore"))

    def scan_usb_speeds(self) -> None:
        self._run_async(self.controller.scan_usb_speeds, self._usb_speed_scan_finished, self._dashboard_text("busy_usb_speed_scan"))

    def _usb_speed_scan_finished(self, count: int, show_message: bool = True) -> None:
        if show_message:
            QMessageBox.information(
                self,
                self._dashboard_text("usb_speed_scan_title"),
                self._dashboard_text("usb_speed_scan_done").format(count=count),
            )
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _initial_usb_speed_scan(self) -> None:
        if self._busy_operations > 0:
            QTimer.singleShot(1000, self._initial_usb_speed_scan)
            return
        self._run_background_async(
            lambda: self.controller.refresh_usb_speed_cache(force=False),
            lambda count: self._background_usb_cache_finished(count, refresh_report=True),
        )

    def _background_usb_cache_finished(self, _count: int, refresh_report: bool = False) -> None:
        if refresh_report and self.controller.last_report:
            self._run_background_async(self.controller.check_now, self.update_report)

    def _poll_game_controllers(self) -> None:
        signature = self.controller.game_controller_signature()
        if signature == self._game_controller_signature:
            return
        self._game_controller_signature = signature
        self.device_change_rescan_timer.start(350)

    def _auto_scan_usb_after_device_change(self) -> None:
        if self._busy_operations > 0:
            self.device_change_rescan_timer.start(1000)
            return
        self._run_background_async(
            lambda: self.controller.scan_usb_speeds(force=True),
            lambda count: self._usb_speed_scan_finished(count, show_message=False),
        )

    def rollback(self) -> None:
        self._run_async(self.controller.rollback_last_restore, self._rollback_finished, self._dashboard_text("busy_rollback"))

    def export_config_backup(self) -> None:
        default_path = Path.home() / self.controller.default_config_backup_name()
        target, _ = QFileDialog.getSaveFileName(
            self,
            self._dashboard_text("export_config_title"),
            str(default_path),
            self._dashboard_text("config_backup_filter"),
        )
        if not target:
            return
        self._run_async(lambda: self.controller.export_config_backup(Path(target)), self._export_config_finished, self._dashboard_text("busy_export"))

    def import_config_backup(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            self._dashboard_text("import_config_title"),
            str(Path.home()),
            self._dashboard_text("config_backup_filter"),
        )
        if not source:
            return
        answer = QMessageBox.question(
            self,
            self._dashboard_text("import_config_title"),
            self._dashboard_text("import_config_confirm"),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run_async(lambda: self.controller.import_config_backup(Path(source)), self._import_config_finished, self._dashboard_text("busy_import"))

    def _restore_finished(self, report: RestoreReport) -> None:
        QMessageBox.information(self, self._dashboard_text("restore_title"), "\n".join(action.message for action in report.actions))
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _rollback_finished(self, action) -> None:
        QMessageBox.information(self, self._dashboard_text("rollback_title"), action.message)
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _export_config_finished(self, path: Path) -> None:
        QMessageBox.information(
            self,
            self._dashboard_text("export_config_title"),
            self._dashboard_text("export_config_done").format(path=path),
        )

    def _import_config_finished(self, backup_path: Path) -> None:
        QMessageBox.information(
            self,
            self._dashboard_text("import_config_title"),
            self._dashboard_text("import_config_done").format(path=backup_path),
        )
        if self.controller.last_report:
            self.update_report(self.controller.last_report)

    def _operation_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Cockpit Guardian", message)

    def update_report(self, report: CheckReport) -> None:
        self._game_controller_signature = self.controller.game_controller_signature()
        self.status_title.setText(self._status_text(report.global_status).upper())
        self._apply_status_style(report.global_status)
        self._update_status_icons(report)
        self.tray.update_report(report)
        self._update_device_table(report)
        self._update_joystick(report)
        self._update_summary(report)
        self._update_quick_log(report)
        self._update_usb(report)
        self._load_priority_table()
        self.refresh_logs()
        self.refresh_advanced()
        QTimer.singleShot(0, self._resize_dashboard_columns)

    def _apply_status_style(self, status: GlobalStatus) -> None:
        color = STATUS_COLORS.get(status, "#6b7280")
        font_size = self._status_font_size(32, 24)
        min_height = 38
        font = self.status_title.font()
        font.setBold(True)
        font.setPixelSize(font_size)
        self.status_title.setFont(font)
        self.status_title.setMinimumHeight(min_height)
        self.status_title.setStyleSheet(
            f"font-size: {font_size}px; font-weight: 800; color: {color}; background: transparent;"
        )

    def _status_font_size(self, desired: int, minimum: int) -> int:
        text = self.status_title.text()
        width = max(1, self.status_title.width() or STATUS_BLOCK_WIDTH)
        font = self.status_title.font()
        font.setBold(True)
        for size in range(desired, minimum - 1, -1):
            font.setPixelSize(size)
            if QFontMetrics(font).horizontalAdvance(text) <= width:
                return size
        return minimum

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
        self.usb_speed_scan_button.setText(self._dashboard_text("usb_speed_scan"))
        self.rollback_button.setText(self._dashboard_text("rollback"))
        self.export_config_button.setText(self._dashboard_text("export"))
        self.import_config_button.setText(self._dashboard_text("import"))
        self.export_config_button.setToolTip(self._dashboard_text("export_config_tooltip"))
        self.import_config_button.setToolTip(self._dashboard_text("import_config_tooltip"))
        self.joystick_up_button.setText(self._dashboard_text("joystick_move_up"))
        self.joystick_down_button.setText(self._dashboard_text("joystick_move_down"))
        self.joystick_properties_button.setText(self._dashboard_text("joystick_properties"))
        self.logo_credit_label.setText(self._dashboard_text("logo_credit"))
        self.language_eng_button.setToolTip(self._dashboard_text("language_en_tooltip"))
        self.language_fr_button.setToolTip(self._dashboard_text("language_fr_tooltip"))
        self.usb_status_label.setText(self._dashboard_text("usb_health"))
        self.com_ports_panel_title.setText(self._dashboard_text("com_ports"))
        self._set_table_headers(self.device_table, self._dashboard_text("device_headers"))
        self._set_table_headers(self.joystick_table, self._dashboard_text("joystick_headers"))
        if hasattr(self, "usb_table"):
            self._set_table_headers(self.usb_table, self._dashboard_text("usb_health_headers"))
        if hasattr(self, "refresh_logs_button"):
            self.refresh_logs_button.setText(self._dashboard_text("refresh_logs"))
            self.export_logs_button.setText(self._dashboard_text("export_logs"))
            self.clear_logs_button.setText(self._dashboard_text("clear_logs"))
        self._refresh_settings_texts()
        self.joystick_panel_title.setText(self._dashboard_text("joystick_order"))
        self.joystick_panel_subtitle.setText(self._dashboard_text("joystick_order_hint"))
        self.quick_log_panel_title.setText(self._dashboard_text("quick_log"))
        tabs = self._dashboard_text("tabs")
        for index, label in enumerate(tabs):
            if index < self.tabs.count():
                self.tabs.setTabText(index, label)
        if self.controller.last_report:
            report = self.controller.last_report
            self._update_status_icons(report)
            self._update_summary(report)
            self._update_quick_log(report)
            self._update_usb(report)
        else:
            self._clear_layout(self.summary_checklist_layout)
            self._set_icon_label(self.usb_status_icon, Severity.INFO)
            self._set_icon_label(self.com_ports_panel_icon, Severity.INFO)
            self._set_icon_label(self.joystick_panel_icon, Severity.INFO)
            self._set_quick_log_lines([self._dashboard_text("no_quick_log")])
        self.footer_prefix_label.setText(self._dashboard_text("footer_prefix"))
        self.footer_label.setText(
            f'<a style="color: #ffffff; text-decoration: none;" href="{YOUTUBE_URL}">REALISTIC SIMCOCKPIT</a>'
        )
        self.footer_version_label.setText(f'| {self._dashboard_text("footer_version")} {__version__}')

    def _refresh_settings_texts(self) -> None:
        if not hasattr(self, "settings_form"):
            return
        form_labels = [
            (self.profile_input, "active_profile"),
            (self.ffb_threshold, "ffb_threshold"),
            (self.notifications, "notifications"),
            (self.launch_startup, "launch_startup"),
            (self.auto_restore, "auto_restore"),
            (self.simhub_required, "simhub_required"),
            (self.deep_windows_scan, "deep_windows_scan"),
            (self.software_scan_interval, "software_scan_cache"),
            (self.usb_health_scan_interval, "usb_health_cache"),
            (self.theme_select, "theme"),
            (self.language_select, "language"),
        ]
        for field, key in form_labels:
            label = self.settings_form.labelForField(field)
            if isinstance(label, QLabel):
                label.setText(self._dashboard_text(key))
        current_theme = self.theme_select.currentData() or self.theme_select.currentText()
        self.theme_select.blockSignals(True)
        self.theme_select.clear()
        for value, label in self._dashboard_text("theme_labels").items():
            self.theme_select.addItem(label, value)
        self._set_combo_data(self.theme_select, str(current_theme))
        self.theme_select.blockSignals(False)
        self.save_settings_button.setText(self._dashboard_text("save_settings"))
        self.priority_label.setText(self._dashboard_text("device_priority"))
        self._set_table_headers(self.priority_table, self._dashboard_text("priority_headers"))

    @staticmethod
    def _set_combo_data(combo: QComboBox, data: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == data or combo.itemText(index) == data:
                combo.setCurrentIndex(index)
                return

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
            device = check.detected or check.expected
            snapshot_device = check.expected or check.detected
            usb_device = check.detected or check.expected
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            usb = self._usb_summary(usb_device)
            detail = check.detail or ""
            if check.ffb_clipping_percent is not None:
                detail = self._dashboard_text("ffb_clipping_detail").format(percent=check.ffb_clipping_percent)
            tooltip = detail or check.message
            label = device.label if device else check.label
            values = [label, self._device_role_text(device), self._device_status_text(check), usb]
            for column, value in enumerate(values):
                item = self._table_item(value)
                item.setToolTip(tooltip)
                if column == 1 and snapshot_device:
                    item.setData(Qt.ItemDataRole.UserRole, snapshot_device.id)
                if column == 2:
                    item.setForeground(QColor(SEVERITY_COLORS.get(check.severity, "#e5e7eb")))
                self.device_table.setItem(row, column, item)

    def _device_role_text(self, device) -> str:
        if not device:
            return self._dashboard_text("unknown")
        return device.custom_role or self._device_kind_text(device.kind)

    def _device_table_cell_double_clicked(self, row: int, column: int) -> None:
        if column == 1:
            cell_rect = self.device_table.visualRect(self.device_table.model().index(row, column))
            self._edit_device_role(row, self.device_table.viewport().mapToGlobal(cell_rect.center()))

    def _device_table_context_requested(self, position) -> None:
        index = self.device_table.indexAt(position)
        if index.isValid() and index.column() == 1:
            self._edit_device_role(index.row(), self.device_table.viewport().mapToGlobal(position))

    def _edit_device_role(self, row: int, global_position=None) -> None:
        item = self.device_table.item(row, 1)
        if item is None:
            return
        device_id = item.data(Qt.ItemDataRole.UserRole)
        if not device_id:
            return
        current = item.text()
        dialog = QInputDialog(self)
        dialog.setWindowTitle(self._dashboard_text("edit_role_title"))
        dialog.setLabelText(self._dashboard_text("edit_role_label"))
        dialog.setTextEchoMode(QLineEdit.EchoMode.Normal)
        dialog.setTextValue(current)
        dialog.resize(260, dialog.sizeHint().height())
        if global_position is not None:
            dialog.move(global_position)
        if not dialog.exec():
            return
        role = dialog.textValue()
        role = " ".join(role.strip().split())
        if not role:
            return
        try:
            self.controller.update_device_role(str(device_id), role)
        except Exception as exc:
            QMessageBox.warning(self, "Cockpit Guardian", str(exc))
            return
        item.setText(role)
        if self.controller.last_report:
            self._update_summary(self.controller.last_report)
            self._load_priority_table()
            self.refresh_advanced()

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
        label = self._usb_label_text(device.usb.label)
        if device.usb.negotiated_speed_mbps:
            return f"{label} - {device.usb.negotiated_speed_mbps} Mbps"
        if device.usb.source and device.usb.source not in {"not detected", "Windows PnP topology", "Windows PnP identity"}:
            return f"{label} - {self._usb_source_text(device.usb.source)}"
        if device.usb.hub_or_port:
            return f"{label} - {self._short_usb_location(device.usb.hub_or_port)}"
        return label

    def _usb_label_text(self, value: str) -> str:
        return self._dashboard_text("usb_labels").get(value, value)

    def _usb_source_text(self, value: str) -> str:
        return self._dashboard_text("usb_sources").get(value, value)

    def _short_usb_location(self, value: str) -> str:
        compact = " ".join(value.replace("|", " ").split())
        if self.settings.language == "fr":
            compact = compact.replace("Root Hub Port", "Port hub racine")
            compact = compact.replace("xHCI Port hub racine", "Port hub racine xHCI")
        if len(compact) <= 34:
            return compact
        return "..." + compact[-31:]

    def _update_joystick(self, report: CheckReport) -> None:
        order = list(report.joystick_order.current or report.joystick_order.expected)
        saved_positions = {name.lower(): str(index) for index, name in enumerate(report.joystick_order.expected, start=1)}
        devices_by_name = self._devices_by_joystick_name(report)
        self.joystick_table.setRowCount(0)
        for index, name in enumerate(order, start=1):
            row = self.joystick_table.rowCount()
            self.joystick_table.insertRow(row)
            device = devices_by_name.get(name.lower())
            game_order = index
            if device and getattr(device, "hid", None):
                game_order = device.hid.game_controller_order or device.hid.joystick_order or index
            self._set_joystick_row(
                row,
                [str(game_order), name, saved_positions.get(name.lower(), "-"), self._usb_summary(device)],
                game_order,
            )
        if not order:
            self.joystick_table.insertRow(0)
            self._set_joystick_row(0, ["-", report.joystick_order.message, "-", "-"], None)

    def _set_joystick_row(self, row: int, values: list[str], game_order: int | None) -> None:
        for column, value in enumerate(values):
            item = self._table_item(value)
            if game_order is not None:
                item.setData(Qt.ItemDataRole.UserRole, game_order)
            self.joystick_table.setItem(row, column, item)

    def _move_selected_joystick(self, delta: int) -> None:
        if not self.joystick_table.move_current_row(delta):
            QMessageBox.warning(self, "Cockpit Guardian", self._dashboard_text("joystick_select_first"))

    def open_selected_joystick_properties(self, row: int | None = None) -> None:
        selected_row = row if row is not None else self.joystick_table.currentRow()
        game_order = self._joystick_row_game_order(selected_row)
        if game_order is None:
            QMessageBox.warning(self, "Cockpit Guardian", self._dashboard_text("joystick_select_first"))
            return
        if not self.controller.open_joystick_properties(game_order):
            QMessageBox.warning(self, "Cockpit Guardian", self._dashboard_text("joystick_properties_failed"))

    def _joystick_row_game_order(self, row: int | None) -> int | None:
        if row is None or row < 0 or row >= self.joystick_table.rowCount():
            return None
        item = self.joystick_table.item(row, 0)
        if not item or item.text() == "-":
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        if value is None:
            value = item.text()
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _joystick_order_changed(self, order: list[str]) -> None:
        try:
            self.controller.update_joystick_order(order)
        except Exception as exc:
            QMessageBox.warning(self, "Cockpit Guardian", str(exc))
            if self.controller.last_report:
                self._update_joystick(self.controller.last_report)
            return
        if self.controller.last_report:
            self._update_status_icons(self.controller.last_report)

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
        summary: dict[str, Severity] = {}
        for check in report.device_checks:
            device = check.detected or check.expected
            if not device:
                continue
            label = self._summary_device_label(device)
            current = summary.get(label)
            summary[label] = check.severity if current is None else self._worst_severity([current, check.severity])
        items = list(summary.items())
        if report.software:
            items.append((self._dashboard_text("software_group"), self._software_summary_severity(report.software)))
        for index, (label, severity) in enumerate(items):
            self._add_checklist_row(self.summary_checklist_layout, index, label, severity)

    def _summary_device_label(self, device) -> str:
        if device.custom_role:
            return device.custom_role
        if device.kind == DeviceKind.OTHER:
            return device.label
        return self._checklist_device_kind_text(device.kind)

    def _update_status_icons(self, report: CheckReport) -> None:
        self.usb_status_row.setVisible(False)
        self._set_icon_label(self.com_ports_panel_icon, self._serial_summary_severity(report))
        self._set_icon_label(self.joystick_panel_icon, Severity.OK if report.joystick_order.ok else Severity.WARNING)

    def _update_quick_log(self, report: CheckReport) -> None:
        lines = []
        if any(check.ffb_clipping_percent is not None for check in report.device_checks):
            lines.append(
                self._dashboard_text("last_ffb_clipping").format(time=self._format_event_time(report.timestamp))
            )
        if report.usb_health.events:
            latest_usb_event = report.usb_health.events[0]
            lines.append(
                self._dashboard_text("last_usb_disconnect").format(time=self._format_event_time(latest_usb_event.timestamp))
            )
        if not lines:
            lines.append(self._dashboard_text("no_quick_log"))
        self._set_quick_log_lines(lines[:2])

    def _set_quick_log_lines(self, lines: list[str]) -> None:
        for index, label in enumerate(self.quick_log_labels):
            text = lines[index] if index < len(lines) else ""
            label.setText(text)
            label.setVisible(bool(text))

    def _format_event_time(self, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "--H--" if self.settings.language == "fr" else "--:--"
        if self.settings.language == "fr":
            return parsed.strftime("%HH%M")
        return parsed.strftime("%H:%M")

    def _add_checklist_row(self, layout: QGridLayout, index: int, label: str, severity: Severity) -> None:
        row = QWidget()
        row.setObjectName("ChecklistRow")
        row.setFixedWidth(CHECKLIST_COLUMN_WIDTH)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(3)
        label_widget = QLabel(label)
        label_widget.setObjectName("ChecklistName")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_widget.setWordWrap(False)
        icon_widget = StatusIconLabel(severity)
        icon_widget.setObjectName("ChecklistIcon")
        row_layout.addWidget(label_widget, 1)
        row_layout.addWidget(icon_widget)
        column = min(index // CHECKLIST_ROWS_PER_COLUMN, CHECKLIST_COLUMNS - 1)
        grid_row = index % CHECKLIST_ROWS_PER_COLUMN
        if index >= CHECKLIST_ROWS_PER_COLUMN * CHECKLIST_COLUMNS:
            grid_row = CHECKLIST_ROWS_PER_COLUMN + index - (CHECKLIST_ROWS_PER_COLUMN * CHECKLIST_COLUMNS)
        layout.addWidget(row, grid_row, column, Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _status_icon(severity: Severity) -> str:
        if severity == Severity.OK:
            return "✓"
        if severity in {Severity.WARNING, Severity.RESTORE_NEEDED, Severity.INFO}:
            return "⚠"
        return "✕"

    def _set_icon_label(self, label: QLabel, severity: Severity) -> None:
        if isinstance(label, StatusIconLabel):
            label.set_severity(severity)
            return
        label.setText(self._status_icon(severity))
        label.setStyleSheet(f"color: {SEVERITY_COLORS.get(severity, '#e5e7eb')};")

    def _serial_summary_severity(self, report: CheckReport) -> Severity:
        severities = [check.severity for check in report.device_checks if self._is_serial_check(check)]
        if not severities:
            return Severity.INFO
        return self._worst_severity(severities)

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
        return cls._worst_severity(cls._severity_from_software_state(item.state) for item in software)

    @staticmethod
    def _worst_severity(severities) -> Severity:
        rank = {
            Severity.OK: 0,
            Severity.INFO: 1,
            Severity.WARNING: 2,
            Severity.RESTORE_NEEDED: 3,
            Severity.CRITICAL: 4,
        }
        worst = Severity.OK
        for severity in severities:
            if rank[severity] > rank[worst]:
                worst = severity
        return worst

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _update_usb(self, report: CheckReport) -> None:
        self.usb_score.setText(self._dashboard_text("usb_health_score").format(score=report.usb_health.stability_score))
        self.usb_table.setRowCount(0)
        for event in report.usb_health.events:
            row = self.usb_table.rowCount()
            self.usb_table.insertRow(row)
            for column, value in enumerate([event.timestamp, self._severity_text(event.severity), event.device_name, event.message]):
                self.usb_table.setItem(row, column, self._table_item(value))

    def save_settings(self) -> None:
        self.settings = Settings(
            profile_name=self.profile_input.text().strip() or "Default Cockpit",
            ffb_clipping_threshold=float(self.ffb_threshold.value()),
            notifications_enabled=self.notifications.isChecked(),
            launch_at_startup=self.launch_startup.isChecked(),
            auto_restore=self.auto_restore.isChecked(),
            theme=str(self.theme_select.currentData() or self.theme_select.currentText()),
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
        QMessageBox.information(self, self._dashboard_text("settings"), self._dashboard_text("settings_saved"))

    def _load_priority_table(self) -> None:
        if not hasattr(self, "priority_table"):
            return
        self.priority_table.setRowCount(0)
        snapshot = self.controller.load_snapshot()
        if not snapshot:
            self.priority_table.insertRow(0)
            self.priority_table.setItem(0, 0, QTableWidgetItem(self._dashboard_text("no_saved_config")))
            self.priority_table.setItem(0, 1, QTableWidgetItem("-"))
            self.priority_table.setItem(0, 2, QTableWidgetItem("-"))
            return
        for device in snapshot.devices:
            row = self.priority_table.rowCount()
            self.priority_table.insertRow(row)
            id_item = QTableWidgetItem(device.label)
            id_item.setData(Qt.ItemDataRole.UserRole, device.id)
            self.priority_table.setItem(row, 0, id_item)
            self.priority_table.setItem(row, 1, QTableWidgetItem(self._device_role_text(device)))
            combo = QComboBox()
            priority_labels = self._dashboard_text("priority_labels")
            for priority in (Priority.REQUIRED, Priority.OPTIONAL, Priority.IGNORED):
                combo.addItem(priority_labels.get(priority, priority.value), priority.value)
            self._set_combo_data(combo, device.priority.value)
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
                priority_by_id[str(device_id)] = Priority(str(combo.currentData() or combo.currentText()))
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

    def clear_logs(self) -> None:
        answer = QMessageBox.question(self, self._dashboard_text("clear_logs"), self._dashboard_text("clear_logs_confirm"))
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.controller.clear_logs()
        self.logs_text.setPlainText("")
        QMessageBox.information(self, self._dashboard_text("clear_logs"), self._dashboard_text("clear_logs_done"))

    def export_logs(self) -> None:
        default_path = self.controller.config.paths.exports / "cockpit_guardian.log"
        target, _ = QFileDialog.getSaveFileName(
            self,
            self._dashboard_text("export_logs"),
            str(default_path),
            self._dashboard_text("log_file_filter"),
        )
        if target:
            self.controller.config.export_logs(Path(target))
            QMessageBox.information(
                self,
                self._dashboard_text("export_logs"),
                self._dashboard_text("logs_exported").format(path=target),
            )

    def refresh_advanced(self) -> None:
        return

    def show_and_raise(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
