"""Generate LinkedIn Featured image (1200x627) matching site hero typography."""
from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_THUMB_OUT", str(ROOT / "images" / "linkedin-featured.png")))

WOFF2_IBM_PLEX_600 = (
    "https://fonts.gstatic.com/s/ibmplexsans/v23/"
    "zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDNF5DB6g4.woff2"
)
WOFF2_SPACE_GROTESK_700 = (
    "https://fonts.gstatic.com/s/spacegrotesk/v22/"
    "V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVnskPMA.woff2"
)

W, H = 1200, 627
MARGIN_X = 180
FG = (0, 0, 0)
BG = (255, 255, 255)


def woff2_to_temp_path(url: str) -> str:
    data = urlopen(url).read()
    font = TTFont(BytesIO(data))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ttf")
    font.save(tmp.name)
    return tmp.name


def draw_tracked_baseline(
    draw: ImageDraw.ImageDraw,
    x: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
    fill: tuple[int, int, int],
) -> None:
    tracking_px = tracking_em * font.size
    cur_x = x
    for i, ch in enumerate(text):
        draw.text((cur_x, baseline_y), ch, font=font, fill=fill, anchor="ls")
        cur_x += font.getlength(ch)
        if i < len(text) - 1:
            cur_x += tracking_px


def tracked_ink_bbox(
    draw: ImageDraw.ImageDraw,
    x: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
) -> tuple[float, float, float, float]:
    """Union of per-glyph ink boxes (anchor=left baseline)."""
    tracking_px = tracking_em * font.size
    cur_x = x
    boxes: list[tuple[float, float, float, float]] = []
    for i, ch in enumerate(text):
        b = draw.textbbox((cur_x, baseline_y), ch, font=font, anchor="ls")
        boxes.append(b)
        cur_x += font.getlength(ch)
        if i < len(text) - 1:
            cur_x += tracking_px
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def align_baseline_to_top(
    draw: ImageDraw.ImageDraw,
    x: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
    want_top: float,
) -> float:
    """Return baseline_y so the ink top of the tracked line equals want_top."""
    baseline_y = want_top + 100.0
    for _ in range(12):
        _l, top, _r, _b = tracked_ink_bbox(draw, x, baseline_y, text, font, tracking_em)
        shift = want_top - top
        baseline_y += shift
        if abs(shift) < 0.25:
            break
    return baseline_y


def main() -> None:
    plex_path = woff2_to_temp_path(WOFF2_IBM_PLEX_600)
    sg_path = woff2_to_temp_path(WOFF2_SPACE_GROTESK_700)
    try:
        eyebrow_size = 23
        name_size = 128
        font_eyebrow = ImageFont.truetype(plex_path, eyebrow_size)
        font_name = ImageFont.truetype(sg_path, name_size)

        eyebrow = "RESEARCHER + BUILDER"
        name = "Robert Spencer"
        gap = 26

        track_eye = 0.16
        track_name = -0.06

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        b_eye = tracked_ink_bbox(draw, float(MARGIN_X), 0.0, eyebrow, font_eyebrow, track_eye)
        b_name = tracked_ink_bbox(draw, float(MARGIN_X), 0.0, name, font_name, track_name)
        block_h = (b_eye[3] - b_eye[1]) + gap + (b_name[3] - b_name[1])
        y_top = (H - block_h) / 2

        baseline_eye = align_baseline_to_top(
            draw, float(MARGIN_X), eyebrow, font_eyebrow, track_eye, y_top
        )
        ink_eye = tracked_ink_bbox(draw, float(MARGIN_X), baseline_eye, eyebrow, font_eyebrow, track_eye)
        want_name_top = ink_eye[3] + gap
        baseline_name = align_baseline_to_top(
            draw, float(MARGIN_X), name, font_name, track_name, want_name_top
        )

        draw_tracked_baseline(draw, float(MARGIN_X), baseline_eye, eyebrow, font_eyebrow, track_eye, FG)
        draw_tracked_baseline(draw, float(MARGIN_X), baseline_name, name, font_name, track_name, FG)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        os.unlink(plex_path)
        os.unlink(sg_path)


if __name__ == "__main__":
    main()
