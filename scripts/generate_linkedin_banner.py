"""LinkedIn profile cover: 1584x396 — eyebrow, name, URL; vertically centred, right-aligned for photo safe zone.

Background matches site body (assets/css/main.css): dark vertical gradient; light text + link accent."""
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
# Render at 2× then downscale with LANCZOS for crisp sub-pixel anti-aliasing.
SCALE = 2
# Inset from the **right** edge. Text is right-aligned so it clears the profile photo
# (large circle on the left on mobile; still looks fine on desktop).
MARGIN_RIGHT = 400


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


def x_right_aligned(
    font: ImageFont.FreeTypeFont,
    text: str,
    tracking_em: float,
    canvas_w: float,
    margin_right: float,
) -> float:
    """Left edge x so the tracked line ends margin_right px before canvas right."""
    return canvas_w - margin_right - tracked_line_width(font, text, tracking_em)


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


def layout_baselines(
    draw: ImageDraw.ImageDraw,
    sw: float,
    margin_right: float,
    font_eyebrow: ImageFont.FreeTypeFont,
    font_name: ImageFont.FreeTypeFont,
    font_url: ImageFont.FreeTypeFont,
    eyebrow: str,
    name: str,
    gap: float,
    gap_after_name: float,
    track_eye: float,
    track_name: float,
    track_url: float,
    y_top: float,
) -> tuple[float, float, float, tuple[float, float, float, float], tuple[float, float, float, float]]:
    """Return eyebrow, name, URL baselines and first/last line ink bboxes (for vertical centering)."""
    x_eye = x_right_aligned(font_eyebrow, eyebrow, track_eye, sw, margin_right)
    baseline_eye = align_baseline_to_top(draw, x_eye, eyebrow, font_eyebrow, track_eye, y_top)
    ink_eye = tracked_ink_bbox(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye)
    want_name_top = ink_eye[3] + gap

    x_name = x_right_aligned(font_name, name, track_name, sw, margin_right)
    baseline_name = align_baseline_to_top(draw, x_name, name, font_name, track_name, want_name_top)
    ink_name = tracked_ink_bbox(draw, x_name, baseline_name, name, font_name, track_name)
    want_url_top = ink_name[3] + gap_after_name

    x_url = x_right_aligned(font_url, SITE_URL, track_url, sw, margin_right)
    baseline_url = align_baseline_to_top(draw, x_url, SITE_URL, font_url, track_url, want_url_top)
    ink_url = tracked_ink_bbox(draw, x_url, baseline_url, SITE_URL, font_url, track_url)
    return baseline_eye, baseline_name, baseline_url, ink_eye, ink_url


def main() -> None:
    plex_600 = woff2_to_temp_path(WOFF2_IBM_PLEX_600)
    plex_400 = woff2_to_temp_path(WOFF2_IBM_PLEX_400)
    sg_path = woff2_to_temp_path(WOFF2_SPACE_GROTESK_700)
    try:
        # All pixel measurements scaled up; canvas downscaled at the end for crisp output.
        sw, sh = W * SCALE, H * SCALE
        margin_right = MARGIN_RIGHT * SCALE

        eyebrow_size = 20 * SCALE
        name_size = 86 * SCALE
        url_size = 24 * SCALE
        font_eyebrow = ImageFont.truetype(plex_600, eyebrow_size)
        font_name = ImageFont.truetype(sg_path, name_size)
        font_url = ImageFont.truetype(plex_400, url_size)

        eyebrow = "RESEARCHER + BUILDER"
        name = "Robert Spencer"
        gap = 22 * SCALE
        gap_after_name = 14 * SCALE

        track_eye = 0.16
        track_name = -0.06
        track_url = 0.05

        img = vertical_site_gradient((sw, sh))
        draw = ImageDraw.Draw(img)

        baseline_eye, baseline_name, baseline_url, ink_eye, ink_url = layout_baselines(
            draw,
            sw,
            margin_right,
            font_eyebrow,
            font_name,
            font_url,
            eyebrow,
            name,
            gap,
            gap_after_name,
            track_eye,
            track_name,
            track_url,
            y_top=0.0,
        )
        block_h = ink_url[3] - ink_eye[1]
        v_shift = (sh - block_h) / 2 - ink_eye[1]
        baseline_eye += v_shift
        baseline_name += v_shift
        baseline_url += v_shift

        x_eye = x_right_aligned(font_eyebrow, eyebrow, track_eye, sw, margin_right)
        x_name = x_right_aligned(font_name, name, track_name, sw, margin_right)
        x_url = x_right_aligned(font_url, SITE_URL, track_url, sw, margin_right)

        draw_tracked_baseline(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye, FG)
        draw_tracked_baseline(draw, x_name, baseline_name, name, font_name, track_name, FG)
        draw_tracked_baseline(draw, x_url, baseline_url, SITE_URL, font_url, track_url, FG_URL)

        # Downscale to the target LinkedIn dimensions with high-quality resampling.
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
