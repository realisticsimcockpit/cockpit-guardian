from cockpit_guardian.services import windows_util


class FakeStartupInfo:
    def __init__(self) -> None:
        self.dwFlags = 0
        self.wShowWindow = None


def test_hidden_subprocess_kwargs_are_empty_off_windows(monkeypatch):
    monkeypatch.setattr(windows_util, "is_windows", lambda: False)

    assert windows_util.hidden_subprocess_kwargs() == {}


def test_hidden_subprocess_kwargs_hide_windows_console(monkeypatch):
    monkeypatch.setattr(windows_util, "is_windows", lambda: True)
    monkeypatch.setattr(windows_util.subprocess, "STARTUPINFO", FakeStartupInfo, raising=False)
    monkeypatch.setattr(windows_util.subprocess, "STARTF_USESHOWWINDOW", 1, raising=False)
    monkeypatch.setattr(windows_util.subprocess, "SW_HIDE", 0, raising=False)
    monkeypatch.setattr(windows_util.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    kwargs = windows_util.hidden_subprocess_kwargs()

    assert kwargs["creationflags"] == 0x08000000
    assert kwargs["startupinfo"].dwFlags & 1
    assert kwargs["startupinfo"].wShowWindow == 0
