from __future__ import annotations

import ctypes
import subprocess
import time
import unicodedata
from ctypes import wintypes

from .windows_util import is_windows


BM_CLICK = 0x00F5
LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_ENSUREVISIBLE = LVM_FIRST + 19
MK_LBUTTON = 0x0001
SW_RESTORE = 9
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
ENUM_WINDOWS_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def open_game_controller_properties(game_controller_order: int, timeout_seconds: float = 4.0) -> bool:
    if not is_windows() or game_controller_order < 1:
        return False
    try:
        subprocess.Popen(["control.exe", "joy.cpl"], close_fds=True)
    except OSError:
        return False

    target_index = game_controller_order - 1
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        dialog = _find_game_controller_dialog()
        if dialog:
            listview = _find_child_by_class(dialog, "SysListView32")
            properties_button = _find_properties_button(dialog)
            if listview and properties_button and _select_listview_row(dialog, listview, target_index):
                user32 = _user32()
                user32.SendMessageW(properties_button, BM_CLICK, 0, 0)
                return True
        time.sleep(0.1)
    return False


def _find_game_controller_dialog() -> int:
    user32 = _user32()
    matches: list[int] = []

    @ENUM_WINDOWS_PROC
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _normalize(_window_text(hwnd))
        if not (
            ("game" in title and "controller" in title)
            or "controleurs de jeu" in title
            or "joystick" in title
        ):
            return True
        if _find_child_by_class(hwnd, "SysListView32") and _find_properties_button(hwnd):
            matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, 0)
    return matches[0] if matches else 0


def _select_listview_row(dialog: int, listview: int, row_index: int) -> bool:
    user32 = _user32()
    count = user32.SendMessageW(listview, LVM_GETITEMCOUNT, 0, 0)
    if row_index < 0 or count <= row_index:
        return False

    user32.ShowWindow(dialog, SW_RESTORE)
    user32.SetForegroundWindow(dialog)
    user32.SendMessageW(listview, LVM_ENSUREVISIBLE, row_index, 0)
    time.sleep(0.05)

    client = wintypes.RECT()
    if not user32.GetClientRect(listview, ctypes.byref(client)):
        return False

    header_height = _child_height(_find_child_by_class(listview, "SysHeader32"))
    row_height = 18
    x = 24
    y = header_height + 9 + (row_index * row_height)
    if y >= client.bottom:
        y = max(header_height + 9, client.bottom - 6)
    lparam = _make_lparam(x, y)
    user32.SetFocus(listview)
    user32.SendMessageW(listview, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
    user32.SendMessageW(listview, WM_LBUTTONUP, 0, lparam)
    time.sleep(0.05)
    return True


def _find_properties_button(parent: int) -> int:
    for button in _find_children_by_class(parent, "Button"):
        text = _normalize(_window_text(button))
        if "properties" in text or "proprietes" in text:
            return button
    return 0


def _find_child_by_class(parent: int, class_name: str) -> int:
    children = _find_children_by_class(parent, class_name)
    return children[0] if children else 0


def _find_children_by_class(parent: int, class_name: str) -> list[int]:
    user32 = _user32()
    matches: list[int] = []

    @ENUM_WINDOWS_PROC
    def callback(hwnd, _lparam):
        if _window_class(hwnd) == class_name:
            matches.append(int(hwnd))
        return True

    user32.EnumChildWindows(parent, callback, 0)
    return matches


def _window_text(hwnd: int) -> str:
    user32 = _user32()
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _window_class(hwnd: int) -> str:
    user32 = _user32()
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def _child_height(hwnd: int) -> int:
    if not hwnd:
        return 0
    rect = wintypes.RECT()
    if not _user32().GetWindowRect(hwnd, ctypes.byref(rect)):
        return 0
    return max(0, rect.bottom - rect.top)


def _make_lparam(x: int, y: int) -> int:
    return (y << 16) | (x & 0xFFFF)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower().replace("&", ""))
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _user32():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.EnumWindows.argtypes = [ENUM_WINDOWS_PROC, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumChildWindows.argtypes = [
        wintypes.HWND,
        ENUM_WINDOWS_PROC,
        wintypes.LPARAM,
    ]
    user32.EnumChildWindows.restype = wintypes.BOOL
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    return user32
