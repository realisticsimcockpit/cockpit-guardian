from importlib.resources import files

from cockpit_guardian.app import SPLASH_HEIGHT, SPLASH_WIDTH


def test_visual_assets_are_packaged():
    assets = files("cockpit_guardian.assets")
    required = [
        "app_icon.ico",
        "app_icon.svg",
        "app_icon_256.png",
        "app_background.png",
        "brand_lockup.png",
        "lang_eng.png",
        "lang_fr.png",
        "spash_screen.mp4",
        "tray_idle.png",
        "tray_ready.png",
        "tray_warning.png",
        "tray_restore.png",
        "tray_critical.png",
        "ui_logo_cg.png",
        "youtube_icon.png",
    ]

    for name in required:
        resource = assets.joinpath(name)
        assert resource.is_file(), name
        assert len(resource.read_bytes()) > 0, name


def test_startup_splash_window_size_matches_requested_design():
    assert (SPLASH_WIDTH, SPLASH_HEIGHT) == (1280, 542)
