"""LinkedIn profile cover: 1584x396 — eyebrow, name, URL; right-aligned for mobile photo safe zone."""
from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_BANNER_OUT", str(ROOT / "images" / "linkedin-banner.png")))

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

# LinkedIn cover (recommended): https://www.linkedin.com/help/linkedin/answer/a568217
W, H = 1584, 396
# Inset from the **right** edge. Text is right-aligned so it clears the profile photo
# (large circle on the left on mobile; still looks fine on desktop).
MARGIN_RIGHT = 400
# Keep the block high in the banner—extra clearance above the photo overlap.
Y_TOP_INSET = 64
FG = (0, 0, 0)
# Near site --text-muted (0.58 black on white)
FG_MUTED = (105, 105, 105)
BG = (255, 255, 255)

SITE_URL = "robertjspencer.com"


def woff2_to_temp_path(url: str) -> str:
    data = urlopen(url).read()
    font = TTFont(BytesIO(data))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ttf")
    font.save(tmp.name)
    return tmp.name


def tracked_line_width(font: ImageFont.FreeTypeFont, text: str, tracking_em: float) -> float:
    if not text:
        return 0.0
    tracking_px = tracking_em * font.size
    total = 0.0
    for i, ch in enumerate(text):
        total += font.getlength(ch)
        if i < len(text) - 1:
            total += tracking_px
    return total


def x_right_aligned(font: ImageFont.FreeTypeFont, text: str, tracking_em: float) -> float:
    """Left edge x so the tracked line ends MARGIN_RIGHT px before canvas right."""
    return float(W) - MARGIN_RIGHT - tracked_line_width(font, text, tracking_em)


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
        eyebrow_size = 20
        name_size = 86
        url_size = 18
        font_eyebrow = ImageFont.truetype(plex_600, eyebrow_size)
        font_name = ImageFont.truetype(sg_path, name_size)
        font_url = ImageFont.truetype(plex_400, url_size)

        eyebrow = "RESEARCHER + BUILDER"
        name = "Robert Spencer"
        gap = 22
        gap_after_name = 14

        track_eye = 0.16
        track_name = -0.06
        track_url = 0.05

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        y_top = float(Y_TOP_INSET)

        x_eye = x_right_aligned(font_eyebrow, eyebrow, track_eye)
        baseline_eye = align_baseline_to_top(draw, x_eye, eyebrow, font_eyebrow, track_eye, y_top)
        ink_eye = tracked_ink_bbox(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye)
        want_name_top = ink_eye[3] + gap

        x_name = x_right_aligned(font_name, name, track_name)
        baseline_name = align_baseline_to_top(draw, x_name, name, font_name, track_name, want_name_top)
        ink_name = tracked_ink_bbox(draw, x_name, baseline_name, name, font_name, track_name)
        want_url_top = ink_name[3] + gap_after_name

        x_url = x_right_aligned(font_url, SITE_URL, track_url)
        baseline_url = align_baseline_to_top(draw, x_url, SITE_URL, font_url, track_url, want_url_top)

        draw_tracked_baseline(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye, FG)
        draw_tracked_baseline(draw, x_name, baseline_name, name, font_name, track_name, FG)
        draw_tracked_baseline(draw, x_url, baseline_url, SITE_URL, font_url, track_url, FG_MUTED)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        os.unlink(plex_600)
        os.unlink(plex_400)
        os.unlink(sg_path)


if __name__ == "__main__":
    main()
