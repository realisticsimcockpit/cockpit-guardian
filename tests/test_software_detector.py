from cockpit_guardian.services.software_detector import SOFTWARE_CATALOG


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
