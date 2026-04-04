"""Generate LinkedIn Featured image (1200x627) matching site hero + banner styling."""
from __future__ import annotations

import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from linkedin_brand import FG, FG_URL, SITE_URL, vertical_site_gradient

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_THUMB_OUT", str(ROOT / "images" / "linkedin-featured.png")))

WOFF2_IBM_PLEX_600 = (
    "https://fonts.gstatic.com/s/ibmplexsans/v23/"
    "zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDNF5DB6g4.woff2"
)
WOFF2_IBM_PLEX_400 = (
    "https://fonts.gstatic.com/s/ibmplexsans/v23/"
    "zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSD6llDB6g4.woff2"
)
WOFF2_SPACE_GROTESK_700 = (
    "https://fonts.gstatic.com/s/spacegrotesk/v22/"
    "V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVnskPMA.woff2"
)

W, H = 1200, 627
# Render at 2× then downscale with LANCZOS for crisp sub-pixel anti-aliasing.
SCALE = 2
MARGIN_X = 180


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
    plex_600 = woff2_to_temp_path(WOFF2_IBM_PLEX_600)
    plex_400 = woff2_to_temp_path(WOFF2_IBM_PLEX_400)
    sg_path = woff2_to_temp_path(WOFF2_SPACE_GROTESK_700)
    try:
        sw, sh = W * SCALE, H * SCALE
        margin_x = float(MARGIN_X * SCALE)

        eyebrow_size = 23 * SCALE
        name_size = 128 * SCALE
        url_size = 21 * SCALE
        font_eyebrow = ImageFont.truetype(plex_600, eyebrow_size)
        font_name = ImageFont.truetype(sg_path, name_size)
        font_url = ImageFont.truetype(plex_400, url_size)

        eyebrow = "RESEARCHER + BUILDER"
        name = "Robert Spencer"
        gap = 26 * SCALE
        gap_after_name = 16 * SCALE

        track_eye = 0.16
        track_name = -0.06
        track_url = 0.05

        img = vertical_site_gradient((sw, sh))
        draw = ImageDraw.Draw(img)

        b_eye = tracked_ink_bbox(draw, margin_x, 0.0, eyebrow, font_eyebrow, track_eye)
        b_name = tracked_ink_bbox(draw, margin_x, 0.0, name, font_name, track_name)
        b_url = tracked_ink_bbox(draw, margin_x, 0.0, SITE_URL, font_url, track_url)
        block_h = (
            (b_eye[3] - b_eye[1])
            + gap
            + (b_name[3] - b_name[1])
            + gap_after_name
            + (b_url[3] - b_url[1])
        )
        y_top = (sh - block_h) / 2

        baseline_eye = align_baseline_to_top(
            draw, margin_x, eyebrow, font_eyebrow, track_eye, y_top
        )
        ink_eye = tracked_ink_bbox(draw, margin_x, baseline_eye, eyebrow, font_eyebrow, track_eye)
        want_name_top = ink_eye[3] + gap
        baseline_name = align_baseline_to_top(
            draw, margin_x, name, font_name, track_name, want_name_top
        )
        ink_name = tracked_ink_bbox(draw, margin_x, baseline_name, name, font_name, track_name)
        want_url_top = ink_name[3] + gap_after_name
        baseline_url = align_baseline_to_top(
            draw, margin_x, SITE_URL, font_url, track_url, want_url_top
        )

        draw_tracked_baseline(draw, margin_x, baseline_eye, eyebrow, font_eyebrow, track_eye, FG)
        draw_tracked_baseline(draw, margin_x, baseline_name, name, font_name, track_name, FG)
        draw_tracked_baseline(draw, margin_x, baseline_url, SITE_URL, font_url, track_url, FG_URL)

        img = img.resize((W, H), Image.LANCZOS)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        os.unlink(plex_600)
        os.unlink(plex_400)
        os.unlink(sg_path)


if __name__ == "__main__":
    main()
