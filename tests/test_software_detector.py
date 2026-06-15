from cockpit_guardian.models import SoftwareState
from cockpit_guardian.services.software_detector import SOFTWARE_CATALOG, SoftwareDetector


def test_vendor_software_catalog_includes_checked_tools():
    expected = {
        "Pimax Play",
        "Meta Quest Link",
        "Fanatec App",
        "SimPro Manager",
        "Moza Pit House",
        "Simucube Tuner",
        "VNM Config",
        "VRS Wheel Tool",
        "Thrustmaster",
        "PXN Racing",
        "CONSPIT Link",
    }

    assert expected.issubset(SOFTWARE_CATALOG)


def test_vendor_software_catalog_has_process_and_display_aliases():
    for name, spec in SOFTWARE_CATALOG.items():
        assert spec["process"], f"{name} has no process aliases"
        assert spec["display"], f"{name} has no installed-app aliases"


def test_simhub_installed_match_prefers_main_app_over_screen_driver():
    installed = {
        "simhub usbd480 1.4.0.0 screen driver": r"C:\Program Files (x86)\USBD480 Screen driver\\",
        "simhub version 9.11.13": r"C:\Program Files (x86)\SimHub\\",
    }

    path = SoftwareDetector._match_installed(["simhub"], installed)

    assert path == r"C:\Program Files (x86)\SimHub\\"


def test_installed_match_handles_names_without_spaces():
    installed = {"pimaxplay version 1.44.2.283": r"C:\Program Files\Pimax\PimaxPlay\\"}

    path = SoftwareDetector._match_installed(["pimax play"], installed)

    assert path == r"C:\Program Files\Pimax\PimaxPlay\\"


def test_installed_app_without_location_is_detected(monkeypatch):
    detector = SoftwareDetector()
    monkeypatch.setattr(SoftwareDetector, "_running_processes", lambda self: set())
    monkeypatch.setattr(SoftwareDetector, "_installed_programs", lambda self, cache_ttl_seconds=300: {"fanatec driver package": ""})

    status = next(item for item in detector.detect() if item.name == "Fanatec App")

    assert status.state == SoftwareState.INSTALLED_CLOSED
    assert status.path is None
