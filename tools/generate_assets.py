from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "src" / "cockpit_guardian" / "assets"

BRAND_BLUE = "#2563eb"
BRAND_GREEN = "#16a34a"
BRAND_ORANGE = "#f97316"
BRAND_RED = "#dc2626"
BRAND_GRAY = "#6b7280"
INK = "#f8fafc"
NIGHT = "#0f172a"


def app_icon_svg(accent: str = BRAND_BLUE) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="104" fill="{NIGHT}"/>
  <path d="M256 58 398 108v122c0 97-56 177-142 224-86-47-142-127-142-224V108L256 58Z" fill="{accent}"/>
  <path d="M256 92 365 130v99c0 75-41 139-109 178-68-39-109-103-109-178v-99L256 92Z" fill="#111827"/>
  <circle cx="256" cy="250" r="94" fill="none" stroke="{INK}" stroke-width="30"/>
  <circle cx="256" cy="250" r="22" fill="{INK}"/>
  <path d="M176 286 120 342" stroke="{INK}" stroke-width="30" stroke-linecap="round"/>
  <path d="M336 286 392 342" stroke="{INK}" stroke-width="30" stroke-linecap="round"/>
  <path d="M256 272v91" stroke="{INK}" stroke-width="30" stroke-linecap="round"/>
  <path d="M199 211c34-22 80-22 114 0" fill="none" stroke="{accent}" stroke-width="22" stroke-linecap="round"/>
</svg>
"""


def tray_svg(color: str, glyph: str) -> str:
    if glyph == "check":
        mark = '<path d="M146 263l67 67 154-172" fill="none" stroke="#ffffff" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>'
    elif glyph == "warning":
        mark = '<path d="M256 132v156" stroke="#ffffff" stroke-width="42" stroke-linecap="round"/><circle cx="256" cy="360" r="24" fill="#ffffff"/>'
    elif glyph == "restore":
        mark = '<path d="M174 198h-62v-62" fill="none" stroke="#ffffff" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/><path d="M124 198c35-62 115-91 185-60 74 33 107 120 74 194s-120 107-194 74" fill="none" stroke="#ffffff" stroke-width="36" stroke-linecap="round"/>'
    elif glyph == "critical":
        mark = '<path d="M180 180l152 152M332 180 180 332" stroke="#ffffff" stroke-width="44" stroke-linecap="round"/>'
    else:
        mark = '<circle cx="256" cy="256" r="34" fill="#ffffff"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="104" fill="{NIGHT}"/>
  <circle cx="256" cy="256" r="172" fill="{color}"/>
  {mark}
</svg>
"""


def logo_lockup_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360">
  <rect width="1200" height="360" rx="36" fill="#ffffff"/>
  <g transform="translate(70 52) scale(.5)">
{app_icon_svg(BRAND_BLUE).replace('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">', '').replace('</svg>', '')}
  </g>
  <text x="370" y="155" font-family="Segoe UI, Arial, sans-serif" font-size="76" font-weight="800" fill="#111827">Cockpit Guardian</text>
  <text x="374" y="220" font-family="Segoe UI, Arial, sans-serif" font-size="31" font-weight="500" fill="#475569">Is your cockpit ready to race?</text>
  <rect x="374" y="252" width="242" height="14" rx="7" fill="{BRAND_BLUE}"/>
</svg>
"""


def write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_svg(svg_path: Path, png_path: Path, size: int) -> None:
    renderer = QSvgRenderer(str(svg_path))
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(png_path)):
        raise RuntimeError(f"Could not write {png_path}")


def render_logo(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    renderer = QSvgRenderer(str(svg_path))
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, width, height))
    painter.end()
    if not image.save(str(png_path)):
        raise RuntimeError(f"Could not write {png_path}")


def render_language_icon(text: str, png_path: Path) -> None:
    image = QImage(96, 48, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#020617"))
    painter.setPen(QColor("#ffffff"))
    painter.drawRoundedRect(QRectF(1, 1, 94, 46), 8, 8)
    painter.setPen(QColor(BRAND_RED))
    painter.drawRoundedRect(QRectF(2.5, 2.5, 91, 43), 7, 7)
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
    painter.drawText(QRectF(0, 0, 96, 44), Qt.AlignmentFlag.AlignCenter, text)
    painter.setPen(QColor(BRAND_RED))
    painter.drawLine(18, 40, 78, 40)
    painter.end()
    if not image.save(str(png_path)):
        raise RuntimeError(f"Could not write {png_path}")


def render_ico(svg_path: Path, ico_path: Path) -> None:
    renderer = QSvgRenderer(str(svg_path))
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, 256, 256))
    painter.end()
    if not image.save(str(ico_path), "ICO"):
        raise RuntimeError(f"Could not write {ico_path}")


def render_preview() -> None:
    items = [
        ("App icon", ASSET_DIR / "app_icon_256.png"),
        ("Tray idle", ASSET_DIR / "tray_idle.png"),
        ("Tray ready", ASSET_DIR / "tray_ready.png"),
        ("Tray warning", ASSET_DIR / "tray_warning.png"),
        ("Tray restore", ASSET_DIR / "tray_restore.png"),
        ("Tray critical", ASSET_DIR / "tray_critical.png"),
    ]
    canvas = QImage(1400, 760, QImage.Format.Format_ARGB32)
    canvas.fill(QColor("#f8fafc"))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#0f172a"))
    painter.setFont(QFont("Arial", 38, QFont.Weight.Bold))
    painter.drawText(48, 70, "Cockpit Guardian visual assets")
    painter.setFont(QFont("Arial", 19))
    painter.setPen(QColor("#475569"))
    painter.drawText(50, 110, "App/taskbar icon, tray states, and brand lockup")
    logo = QImage(str(ASSET_DIR / "brand_lockup.png"))
    painter.drawImage(QRectF(50, 145, 600, 180), logo)
    x = 70
    for label, path in items:
        image = QImage(str(path))
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QColor("#e2e8f0"))
        painter.drawRoundedRect(QRectF(x - 22, 390, 180, 250), 16, 16)
        painter.drawImage(QRectF(x, 420, 136, 136), image)
        painter.setPen(QColor("#0f172a"))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(QRectF(x - 10, 575, 156, 46), Qt.AlignmentFlag.AlignCenter, label)
        x += 215
    painter.end()
    if not canvas.save(str(ASSET_DIR / "asset_preview.png")):
        raise RuntimeError("Could not write asset preview")


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    app_svg = ASSET_DIR / "app_icon.svg"
    logo_svg = ASSET_DIR / "brand_lockup.svg"
    write_svg(app_svg, app_icon_svg())
    write_svg(logo_svg, logo_lockup_svg())
    render_svg(app_svg, ASSET_DIR / "app_icon_256.png", 256)
    render_svg(app_svg, ASSET_DIR / "app_icon_64.png", 64)
    render_ico(app_svg, ASSET_DIR / "app_icon.ico")
    render_logo(logo_svg, ASSET_DIR / "brand_lockup.png", 1200, 360)

    tray_specs = {
        "tray_idle": (BRAND_GRAY, "idle"),
        "tray_ready": (BRAND_GREEN, "check"),
        "tray_warning": (BRAND_ORANGE, "warning"),
        "tray_restore": (BRAND_ORANGE, "restore"),
        "tray_critical": (BRAND_RED, "critical"),
    }
    for name, (color, glyph) in tray_specs.items():
        svg = ASSET_DIR / f"{name}.svg"
        write_svg(svg, tray_svg(color, glyph))
        render_svg(svg, ASSET_DIR / f"{name}.png", 64)

    render_language_icon("ENG", ASSET_DIR / "lang_eng.png")
    render_language_icon("FR", ASSET_DIR / "lang_fr.png")
    render_preview()
    print(f"Generated assets in {ASSET_DIR}")
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
