from __future__ import annotations

import ctypes
from dataclasses import dataclass
from ctypes import wintypes

from .windows_util import is_windows


def _ctl_code(device_type: int, function: int, method: int = 0, access: int = 0) -> int:
    return (device_type << 16) | (access << 14) | (function << 2) | method


FILE_DEVICE_USB = 0x22
IOCTL_USB_GET_NODE_INFORMATION = _ctl_code(FILE_DEVICE_USB, 258)
IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX = _ctl_code(FILE_DEVICE_USB, 274)
IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX_V2 = _ctl_code(FILE_DEVICE_USB, 279)

DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
GENERIC_WRITE = 0x40000000
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
ERROR_NO_MORE_ITEMS = 259
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

USB_SPEEDS = {
    0: ("USB Low-Speed", "USB 1.1", 1),
    1: ("USB Full-Speed", "USB 1.1", 12),
    2: ("USB High-Speed", "USB 2.0", 480),
    3: ("USB SuperSpeed", "USB 3.x", 5000),
}


@dataclass(frozen=True, slots=True)
class UsbSpeedRecord:
    vid: str
    pid: str
    label: str
    usb_generation: str
    negotiated_speed_mbps: int
    hub_path: str
    port: int
    confidence: str = "high"
    source: str = "USB hub speed scan"
    note: str = "Speed read from Windows USB hub IOCTLs."

    @property
    def vid_pid(self) -> str:
        return f"{self.vid}:{self.pid}"

    def to_dict(self) -> dict[str, object]:
        return {
            "vid": self.vid,
            "pid": self.pid,
            "label": self.label,
            "usb_generation": self.usb_generation,
            "negotiated_speed_mbps": self.negotiated_speed_mbps,
            "hub_path": self.hub_path,
            "port": self.port,
            "confidence": self.confidence,
            "source": self.source,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "UsbSpeedRecord | None":
        try:
            vid = str(data["vid"]).upper()
            pid = str(data["pid"]).upper()
            label = str(data["label"])
            usb_generation = str(data["usb_generation"])
            negotiated_speed_mbps = int(data["negotiated_speed_mbps"])
            hub_path = str(data.get("hub_path") or "")
            port = int(data.get("port") or 0)
        except Exception:
            return None
        return cls(
            vid=vid,
            pid=pid,
            label=label,
            usb_generation=usb_generation,
            negotiated_speed_mbps=negotiated_speed_mbps,
            hub_path=hub_path,
            port=port,
            confidence=str(data.get("confidence") or "high"),
            source=str(data.get("source") or "USB hub speed scan"),
            note=str(data.get("note") or "Speed read from Windows USB hub IOCTLs."),
        )


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


def _guid(data1: int, data2: int, data3: int, *data4: int) -> GUID:
    return GUID(data1, data2, data3, (wintypes.BYTE * 8)(*data4))


GUID_DEVINTERFACE_USB_HUB = _guid(0xF18A0E88, 0xC30C, 0x11D0, 0x88, 0x15, 0x00, 0xA0, 0xC9, 0x06, 0xBE, 0xD8)


class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


class SP_DEVICE_INTERFACE_DETAIL_DATA_W(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("DevicePath", wintypes.WCHAR * 1024)]


class USB_HUB_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("bDescriptorLength", wintypes.BYTE),
        ("bDescriptorType", wintypes.BYTE),
        ("bNumberOfPorts", wintypes.BYTE),
        ("wHubCharacteristics", wintypes.USHORT),
        ("bPowerOnToPowerGood", wintypes.BYTE),
        ("bHubControlCurrent", wintypes.BYTE),
        ("bRemoveAndPowerMask", wintypes.BYTE * 64),
    ]


class USB_HUB_INFORMATION(ctypes.Structure):
    _fields_ = [("HubDescriptor", USB_HUB_DESCRIPTOR), ("HubIsBusPowered", wintypes.BOOL)]


class USB_MI_PARENT_INFORMATION(ctypes.Structure):
    _fields_ = [("NumberOfInterfaces", wintypes.ULONG)]


class USB_NODE_INFORMATION_U(ctypes.Union):
    _fields_ = [("HubInformation", USB_HUB_INFORMATION), ("MiParentInformation", USB_MI_PARENT_INFORMATION)]


class USB_NODE_INFORMATION(ctypes.Structure):
    _fields_ = [("NodeType", ctypes.c_int), ("u", USB_NODE_INFORMATION_U)]


class USB_DEVICE_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("bLength", wintypes.BYTE),
        ("bDescriptorType", wintypes.BYTE),
        ("bcdUSB", wintypes.USHORT),
        ("bDeviceClass", wintypes.BYTE),
        ("bDeviceSubClass", wintypes.BYTE),
        ("bDeviceProtocol", wintypes.BYTE),
        ("bMaxPacketSize0", wintypes.BYTE),
        ("idVendor", wintypes.USHORT),
        ("idProduct", wintypes.USHORT),
        ("bcdDevice", wintypes.USHORT),
        ("iManufacturer", wintypes.BYTE),
        ("iProduct", wintypes.BYTE),
        ("iSerialNumber", wintypes.BYTE),
        ("bNumConfigurations", wintypes.BYTE),
    ]


class USB_ENDPOINT_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("bLength", wintypes.BYTE),
        ("bDescriptorType", wintypes.BYTE),
        ("bEndpointAddress", wintypes.BYTE),
        ("bmAttributes", wintypes.BYTE),
        ("wMaxPacketSize", wintypes.USHORT),
        ("bInterval", wintypes.BYTE),
    ]


class USB_PIPE_INFO(ctypes.Structure):
    _fields_ = [("EndpointDescriptor", USB_ENDPOINT_DESCRIPTOR), ("ScheduleOffset", wintypes.ULONG)]


class USB_NODE_CONNECTION_INFORMATION_EX(ctypes.Structure):
    _fields_ = [
        ("ConnectionIndex", wintypes.ULONG),
        ("DeviceDescriptor", USB_DEVICE_DESCRIPTOR),
        ("CurrentConfigurationValue", wintypes.BYTE),
        ("Speed", wintypes.BYTE),
        ("DeviceIsHub", wintypes.BYTE),
        ("DeviceAddress", wintypes.USHORT),
        ("NumberOfOpenPipes", wintypes.ULONG),
        ("ConnectionStatus", wintypes.ULONG),
        ("PipeList", USB_PIPE_INFO * 30),
    ]


class USB_NODE_CONNECTION_INFORMATION_EX_V2(ctypes.Structure):
    _fields_ = [
        ("ConnectionIndex", wintypes.ULONG),
        ("Length", wintypes.ULONG),
        ("SupportedUsbProtocols", wintypes.ULONG),
        ("Flags", wintypes.ULONG),
    ]


class UsbSpeedScanner:
    """USBView-style hub speed scanner.

    Microsoft USBView uses the same family of hub IOCTLs. This scanner keeps the
    subset Cockpit Guardian needs: VID/PID, hub port, and negotiated speed.
    """

    def __init__(self) -> None:
        self._setupapi = None
        self._kernel32 = None

    def scan(self) -> list[UsbSpeedRecord]:
        if not is_windows():
            return []
        self._load_dlls()
        records: list[UsbSpeedRecord] = []
        for hub_path in self._hub_paths():
            records.extend(self._scan_hub(hub_path))
        return records

    def _load_dlls(self) -> None:
        if self._setupapi is not None and self._kernel32 is not None:
            return
        self._setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
        self._setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE
        self._setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
            wintypes.HANDLE,
            ctypes.c_void_p,
            ctypes.POINTER(GUID),
            wintypes.DWORD,
            ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
        ]
        self._setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
        self._setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
            ctypes.POINTER(SP_DEVICE_INTERFACE_DETAIL_DATA_W),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(SP_DEVINFO_DATA),
        ]
        self._setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
        self._setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
        self._setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
        self._kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        self._kernel32.CreateFileW.restype = wintypes.HANDLE
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.DeviceIoControl.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.c_void_p,
        ]
        self._kernel32.DeviceIoControl.restype = wintypes.BOOL

    def _hub_paths(self) -> list[str]:
        device_info = self._setupapi.SetupDiGetClassDevsW(
            ctypes.byref(GUID_DEVINTERFACE_USB_HUB),
            None,
            None,
            DIGCF_PRESENT | DIGCF_DEVICEINTERFACE,
        )
        if device_info == INVALID_HANDLE_VALUE:
            return []
        paths: list[str] = []
        index = 0
        try:
            while True:
                interface_data = SP_DEVICE_INTERFACE_DATA()
                interface_data.cbSize = ctypes.sizeof(interface_data)
                ok = self._setupapi.SetupDiEnumDeviceInterfaces(
                    device_info,
                    None,
                    ctypes.byref(GUID_DEVINTERFACE_USB_HUB),
                    index,
                    ctypes.byref(interface_data),
                )
                if not ok:
                    if ctypes.get_last_error() == ERROR_NO_MORE_ITEMS:
                        break
                    return paths
                required = wintypes.DWORD()
                self._setupapi.SetupDiGetDeviceInterfaceDetailW(
                    device_info,
                    ctypes.byref(interface_data),
                    None,
                    0,
                    ctypes.byref(required),
                    None,
                )
                detail = SP_DEVICE_INTERFACE_DETAIL_DATA_W()
                detail.cbSize = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
                devinfo = SP_DEVINFO_DATA()
                devinfo.cbSize = ctypes.sizeof(devinfo)
                ok = self._setupapi.SetupDiGetDeviceInterfaceDetailW(
                    device_info,
                    ctypes.byref(interface_data),
                    ctypes.byref(detail),
                    ctypes.sizeof(detail),
                    ctypes.byref(required),
                    ctypes.byref(devinfo),
                )
                if ok and detail.DevicePath:
                    paths.append(str(detail.DevicePath))
                index += 1
        finally:
            self._setupapi.SetupDiDestroyDeviceInfoList(device_info)
        return paths

    def _scan_hub(self, hub_path: str) -> list[UsbSpeedRecord]:
        handle = self._kernel32.CreateFileW(hub_path, GENERIC_WRITE, FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
        if handle == INVALID_HANDLE_VALUE:
            return []
        try:
            port_count = self._hub_port_count(handle)
            records: list[UsbSpeedRecord] = []
            for port in range(1, port_count + 1):
                record = self._scan_port(handle, hub_path, port)
                if record is not None:
                    records.append(record)
            return records
        finally:
            self._kernel32.CloseHandle(handle)

    def _hub_port_count(self, handle) -> int:
        info = USB_NODE_INFORMATION()
        info.NodeType = 0
        bytes_returned = wintypes.DWORD()
        ok = self._kernel32.DeviceIoControl(
            handle,
            IOCTL_USB_GET_NODE_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
            ctypes.byref(info),
            ctypes.sizeof(info),
            ctypes.byref(bytes_returned),
            None,
        )
        if not ok:
            return 0
        return int(info.u.HubInformation.HubDescriptor.bNumberOfPorts)

    def _scan_port(self, handle, hub_path: str, port: int) -> UsbSpeedRecord | None:
        info = USB_NODE_CONNECTION_INFORMATION_EX()
        info.ConnectionIndex = port
        bytes_returned = wintypes.DWORD()
        ok = self._kernel32.DeviceIoControl(
            handle,
            IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX,
            ctypes.byref(info),
            ctypes.sizeof(info),
            ctypes.byref(info),
            ctypes.sizeof(info),
            ctypes.byref(bytes_returned),
            None,
        )
        if not ok:
            return None
        vid = int(info.DeviceDescriptor.idVendor)
        pid = int(info.DeviceDescriptor.idProduct)
        if not vid or not pid:
            return None
        label, generation, speed = self._speed_from_info(handle, port, int(info.Speed))
        return UsbSpeedRecord(
            vid=f"{vid:04X}",
            pid=f"{pid:04X}",
            label=label,
            usb_generation=generation,
            negotiated_speed_mbps=speed,
            hub_path=hub_path,
            port=port,
        )

    def _speed_from_info(self, handle, port: int, speed_code: int) -> tuple[str, str, int]:
        v2 = USB_NODE_CONNECTION_INFORMATION_EX_V2()
        v2.ConnectionIndex = port
        v2.Length = ctypes.sizeof(v2)
        v2.SupportedUsbProtocols = 0x7
        bytes_returned = wintypes.DWORD()
        ok = self._kernel32.DeviceIoControl(
            handle,
            IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX_V2,
            ctypes.byref(v2),
            ctypes.sizeof(v2),
            ctypes.byref(v2),
            ctypes.sizeof(v2),
            ctypes.byref(bytes_returned),
            None,
        )
        if ok and int(v2.Flags) & 0x4:
            return "USB SuperSpeedPlus", "USB 3.x", 10000
        if ok and int(v2.Flags) & 0x1:
            return "USB SuperSpeed", "USB 3.x", 5000
        return USB_SPEEDS.get(speed_code, ("USB speed unknown", "unknown", 0))
