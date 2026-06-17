from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from uuid import UUID

from .windows_util import is_windows


DIRECTINPUT_VERSION = 0x0800
DI8DEVCLASS_GAMECTRL = 4
DIEDFL_ATTACHEDONLY = 0x00000001
DIENUM_CONTINUE = 1
IID_IDIRECTINPUT8W = "BF798031-483A-4DA2-AA99-5D64ED369700"


@dataclass(frozen=True, slots=True)
class DirectInputGameController:
    order: int
    product_name: str
    instance_name: str
    vid: str | None
    pid: str | None
    product_guid: str
    instance_guid: str


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __str__(self) -> str:
        data4 = bytes(self.Data4)
        return (
            f"{int(self.Data1):08X}-{int(self.Data2):04X}-{int(self.Data3):04X}-"
            f"{data4[0]:02X}{data4[1]:02X}-{data4[2:].hex().upper()}"
        )


class _DIDEVICEINSTANCEW(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("guidInstance", _GUID),
        ("guidProduct", _GUID),
        ("dwDevType", wintypes.DWORD),
        ("tszInstanceName", wintypes.WCHAR * 260),
        ("tszProductName", wintypes.WCHAR * 260),
        ("guidFFDriver", _GUID),
        ("wUsagePage", wintypes.WORD),
        ("wUsage", wintypes.WORD),
    ]


_ENUM_CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.POINTER(_DIDEVICEINSTANCEW), ctypes.c_void_p)


def read_directinput_game_controllers() -> list[DirectInputGameController]:
    if not is_windows():
        return []
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        dinput = ctypes.WinDLL("dinput8", use_last_error=True)
    except OSError:
        return []

    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    dinput.DirectInput8Create.restype = ctypes.c_long
    dinput.DirectInput8Create.argtypes = [
        wintypes.HINSTANCE,
        wintypes.DWORD,
        ctypes.POINTER(_GUID),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
    ]

    interface_id = _guid_from_string(IID_IDIRECTINPUT8W)
    directinput = ctypes.c_void_p()
    result = dinput.DirectInput8Create(
        kernel32.GetModuleHandleW(None),
        DIRECTINPUT_VERSION,
        ctypes.byref(interface_id),
        ctypes.byref(directinput),
        None,
    )
    if result != 0 or not directinput.value:
        return []

    controllers: list[DirectInputGameController] = []
    try:
        vtable = ctypes.cast(directinput, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        enum_devices = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            wintypes.DWORD,
            _ENUM_CALLBACK,
            ctypes.c_void_p,
            wintypes.DWORD,
        )(vtable[4])
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])

        @_ENUM_CALLBACK
        def callback(instance, _ref):
            device = instance.contents
            vid, pid = _vid_pid_from_product_guid(device.guidProduct)
            controllers.append(
                DirectInputGameController(
                    order=len(controllers) + 1,
                    product_name=str(device.tszProductName or "").strip(),
                    instance_name=str(device.tszInstanceName or "").strip(),
                    vid=vid,
                    pid=pid,
                    product_guid=str(device.guidProduct),
                    instance_guid=str(device.guidInstance),
                )
            )
            return DIENUM_CONTINUE

        enum_devices(directinput, DI8DEVCLASS_GAMECTRL, callback, None, DIEDFL_ATTACHEDONLY)
        release(directinput)
    except Exception:
        return []
    return controllers


def _guid_from_string(value: str) -> _GUID:
    return _GUID.from_buffer_copy(UUID(value).bytes_le)


def _vid_pid_from_product_guid(guid: _GUID) -> tuple[str | None, str | None]:
    data1 = int(guid.Data1)
    vid = data1 & 0xFFFF
    pid = (data1 >> 16) & 0xFFFF
    if not vid or not pid:
        return None, None
    return f"{vid:04X}", f"{pid:04X}"
