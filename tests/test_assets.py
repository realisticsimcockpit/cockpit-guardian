from importlib.resources import files


def test_visual_assets_are_packaged():
    assets = files("cockpit_guardian.assets")
    required = [
        "app_icon.ico",
        "app_icon.svg",
        "app_icon_256.png",
        "app_background.png",
        "brand_lockup.png",
        "tray_idle.png",
        "tray_ready.png",
        "tray_warning.png",
        "tray_restore.png",
        "tray_critical.png",
        "ui_logo_cg.png",
    ]

    for name in required:
        resource = assets.joinpath(name)
        assert resource.is_file(), name
        assert len(resource.read_bytes()) > 0, name
