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


def test_run_powershell_json_requests_utf8(monkeypatch):
    calls = {}

    class Completed:
        returncode = 0
        stdout = '{"Name": "Périphérique série USB"}'

    def fake_run(command, **kwargs):
        calls["command"] = command
        calls["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr(windows_util, "is_windows", lambda: True)
    monkeypatch.setattr(windows_util, "hidden_subprocess_kwargs", lambda: {})
    monkeypatch.setattr(windows_util.subprocess, "run", fake_run)

    rows = windows_util.run_powershell_json("Get-Device")

    assert rows == [{"Name": "Périphérique série USB"}]
    assert calls["kwargs"]["encoding"] == "utf-8"
    assert "[Console]::OutputEncoding" in " ".join(calls["command"])
