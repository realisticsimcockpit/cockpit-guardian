import struct

from cockpit_guardian.services.telemetry import TelemetryService


def test_environment_override_reports_clipping(monkeypatch):
    monkeypatch.setenv("COCKPIT_GUARDIAN_FFB_CLIPPING", "22")

    status = TelemetryService().get_status([])

    assert status.available is True
    assert status.ffb_clipping_percent == 22.0
    assert status.source == "Telemetry override"


def test_iracing_parser_reads_steering_wheel_pct_torque():
    data = bytearray(1024)
    struct.pack_into(
        "<12i",
        data,
        0,
        2,  # version
        1,  # connected
        60,
        0,
        0,
        0,
        1,  # num vars
        112,  # var header offset
        1,  # num buffers
        256,  # buffer length
        0,
        0,
    )
    struct.pack_into("<2i", data, 48, 42, 512)
    name = b"SteeringWheelPctTorque"
    struct.pack_into("<iii?3x32s64s32s", data, 112, 4, 0, 1, False, name, b"", b"%")
    struct.pack_into("<f", data, 512, -0.99)

    status = TelemetryService()._parse_iracing(bytes(data))

    assert status.available is True
    assert status.source == "iRacing"
    assert round(status.ffb_signal_percent) == 99
    assert status.ffb_clipping_percent == 100.0


def test_iracing_parser_ignores_empty_stale_map():
    status = TelemetryService()._parse_iracing(bytes(1024))

    assert status.available is False


def test_signal_window_computes_clipping_percentage():
    service = TelemetryService(window_size=4)

    service._status_from_signal("Test", 50.0, 0.5)
    service._status_from_signal("Test", 99.0, 0.99)
    service._status_from_signal("Test", 99.0, 0.99)
    status = service._status_from_signal("Test", 20.0, 0.2)

    assert status.ffb_clipping_percent == 50.0
