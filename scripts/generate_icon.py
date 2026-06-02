"""Generate .ico files for the installer and window icon.

Reads frontend/public/favicon.svg as the canonical source.
Outputs:
  - build/icon.ico          (256×256 multi-res ICO for installer + pywebview)
  - frontend/public/favicon.ico  (same, for browser fallback)
"""

from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
SVG_PATH = BASE_DIR / "frontend" / "public" / "favicon.svg"
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def _draw_house(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colour palette
    roof_dark = (21, 48, 86)      # #153056
    roof_light = (43, 108, 176)   # #2b6cb0
    wall = (247, 250, 252)        # #f7fafc

    # Geometry (normalised to 64×64 then scaled)
    def s(v: float) -> int | float:
        return v * size / 64

    # Roof (polygon: peak at 32,4 → bottom at 4,24 and 60,24)
    draw.polygon([
        (s(32), s(4)),
        (s(4), s(24)),
        (s(60), s(24)),
    ], fill=roof_light, outline=roof_dark, width=max(1, int(s(2))))

    # Roof extension down to bottom (covers wall area under roof slope)
    draw.polygon([
        (s(32), s(4)),
        (s(4), s(24)),
        (s(4), s(60)),
        (s(60), s(60)),
        (s(60), s(24)),
    ], fill=None, outline=None)

    # Wall (rectangle under roof)
    draw.rectangle([s(10), s(24), s(54), s(60)], fill=wall)

    # Roof outline again on top
    draw.polygon([
        (s(32), s(4)),
        (s(4), s(24)),
        (s(60), s(24)),
    ], fill=roof_light, outline=roof_dark, width=max(1, int(s(2))))

    # Roof bottom edge line
    draw.line([s(4), s(24), s(60), s(24)], fill=roof_dark, width=max(1, int(s(2))))

    # Door
    door_x, door_w = s(24), s(16)
    door_y, door_h = s(32), s(28)
    draw.rounded_rectangle(
        [door_x, door_y, door_x + door_w, door_y + door_h],
        radius=max(1, int(s(2))), fill=roof_light,
        outline=roof_dark, width=max(1, int(s(1.5))),
    )

    # Windows (two small squares)
    for wx in [s(13), s(44)]:
        wy, ww, wh = s(30), s(7), s(7)
        draw.rounded_rectangle(
            [wx, wy, wx + ww, wy + wh],
            radius=max(1, int(s(1.5))), fill=roof_light,
            outline=roof_dark, width=max(1, int(s(1.5))),
        )

    return img


def _save_ico(path: Path, sizes: list[int]):
    master = _draw_house(max(sizes))
    master.save(path, format="ICO", sizes=[(sz, sz) for sz in sizes])


def main():
    out_dir = BASE_DIR / "build"
    out_dir.mkdir(parents=True, exist_ok=True)

    ico_path = out_dir / "icon.ico"
    _save_ico(ico_path, ICO_SIZES)
    print(f"  Icon: {ico_path} ({ico_path.stat().st_size / 1024:.1f} KB)")

    public_dir = BASE_DIR / "frontend" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    public_ico = public_dir / "favicon.ico"
    _save_ico(public_ico, [16, 32, 48])
    print(f"  Favicon: {public_ico} ({public_ico.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
